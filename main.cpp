
////////////////////////     DIFFERENT APPROACH HNDLE MOVE FUNCTION  VIA MAIN LOOP //////////////////////////
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Stepper.h>

// WiFi settings
const char* ssid = "StepperControl";
const char* password = "12345678";

// Stepper motor pins for ULN2003 driver
#define IN1 D1
#define IN2 D2
#define IN3 D3
#define IN4 D4
#define LIMIT_SWITCH_PIN D5  // Limit switch for homing

// Movement state
volatile bool isMoving = false;
volatile bool isHomed = false;
volatile float currentPosition = -1; // Current position of the stepper motor


// Steps per revolution for 28BYJ-48 motor
const int STEPS_PER_REVOLUTION = 111550;  // 32 steps per revolution * 64:1 gearbox
const float STEPS_PER_DEGREE = 310 ;//STEPS_PER_REVOLUTION / 360.0;
const bool CALIBRATE = false;

// Initialize stepper motor
Stepper stepper(STEPS_PER_REVOLUTION, IN1, IN3, IN2, IN4);
ESP8266WebServer server(80);

// Movement variables
float targetAngle = 0;
int stepsPerSegment = 0;
unsigned long previousTime = 0;
unsigned long delayTime = 0;

// Function declarations
void moveStepper(int steps);
void updateMovement();
long calibrateStepsPerRevolution();

// HTML page with input form
const char* html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>Antenna Mapper</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 50px auto; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        .input-group { margin: 15px 0; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
        input { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 10px; font-size: 18px; color: #fff; background-color: #007bff; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; }
        button.stop { background-color: #ff6b6b; }
        button:hover { opacity: 0.9; }
        #status, #current-position { margin: 15px 0; padding: 10px; background-color: #e9ecef; border-radius: 5px; text-align: center; font-size: 18px; }
    </style>
    <script>
        function checkStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = 'System Status: ' + data.status;
                    document.getElementById('current-position').textContent = 'Current Position: ' + data.currentAngle.toFixed(2) + '°';
                });
        }

        function sendCommand(endpoint) {
            fetch(endpoint).then(() => checkStatus());
        }

        function startMovement(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const params = new URLSearchParams(formData).toString();
            fetch('/move?' + params)
                .then(() => checkStatus());
        }

        setInterval(checkStatus, 1000); // Update status every second
    </script>
</head>
<body>
    <div class="container">
        <h1>Antenna Positioning System</h1>
        <div id="status">System Status: Ready</div>
        <div id="current-position">Current Position: 0°</div>
        <button onclick="sendCommand('/home')">Set Zero Position</button>
        <button onclick="sendCommand('/stop')" class="stop">Emergency Stop</button>
        <form onsubmit="startMovement(event)">
            <div class="input-group">
                <label for="angle">Target Angle:</label>
                <input type="number" id="angle" name="angle" required>
            </div>
            <div class="input-group">
                <label for="stepSize">Step Size:</label>
                <input type="number" id="stepSize" name="stepSize" required>
            </div>
            <div class="input-group">
                <label for="delay">Delay (seconds):</label>
                <input type="number" id="delay" name="delay" required>
            </div>
            <button type="submit">Start Mapping</button>
        </form>
    </div>
</body>
</html>
)rawliteral";

// Web server handlers
void handleRoot() {
    server.send(200, "text/html", html);
}

void handleStatus() {
    String status = "{";
    status += "\"status\":\"" + String(isHomed ? (isMoving ? "Moving" : "Ready") : "Not Homed") + "\",";
    status += "\"currentAngle\":" + String(currentPosition) + "}";
    server.send(200, "application/json", status);
}

void handleStop() {
    isMoving = false;
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    server.send(200, "text/plain", "Stopped");
}

void handleHome() {
    if (isMoving) {
        server.send(400, "text/plain", "System is currently moving");
        return;
    }

    isMoving = true;
    currentPosition = 0;

    // Move the motor until the limit switch is triggered
    while (digitalRead(LIMIT_SWITCH_PIN) && isMoving) {
        stepper.step(-1);
        delay(5);
    }

    if (isMoving) {
        isHomed = true;
    }

    isMoving = false;
    server.send(200, "text/plain", "Homing complete");
}

void handleMove() {
    if (!isHomed) {
        server.send(400, "text/plain", "Please home the system first");
        return;
    }

    if (isMoving) {
        server.send(400, "text/plain", "System is currently moving");
        return;
    }

    targetAngle = server.arg("angle").toFloat();
    int stepSize = server.arg("stepSize").toInt();
    delayTime = server.arg("delay").toInt() * 1000;

    if (targetAngle <= 0 || stepSize <= 0 || delayTime < 0) {
        server.send(400, "text/plain", "Invalid parameters");
        return;
    }

    server.send(200, "text/plain", "Mapping started");
    isMoving = true;
    stepsPerSegment = round(stepSize * STEPS_PER_DEGREE);
    previousTime = millis();
}

void setup() {
    Serial.begin(9600);
    pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
    WiFi.softAP(ssid, password);

    server.on("/", handleRoot);
    server.on("/move", handleMove);
    server.on("/home", handleHome);
    server.on("/stop", handleStop);
    server.on("/status", handleStatus);

    //caibration
    if(CALIBRATE){
        long stepsPerRevolution = calibrateStepsPerRevolution();
        Serial.println("Calibration complete");
        Serial.printf("Steps per revolution: %ld\n", stepsPerRevolution);
    }


    server.begin();
    stepper.setSpeed(10);
    isHomed = false;
    isMoving = false;
    
}

// Update motor movement in loop
void updateMovement() {
    if (isMoving && currentPosition < targetAngle) {
        // Check if the elapsed time is greater or equal to the delay time set
        if (millis() - previousTime >= delayTime) {
            Serial.printf("End of brake");

            // Update the current position and move the stepper motor
            currentPosition += stepsPerSegment / STEPS_PER_DEGREE;
            moveStepper(stepsPerSegment);

            // Print a message indicating the start of the delay after moving the stepper
            
            Serial.printf("Start brake, current position: %.2f\n", currentPosition);

            // Update the last step time
            previousTime = millis();
        }

        // yield() allows background tasks (e.g., WiFi tasks) during the wait
        yield();
    }

    // Stop moving if target angle is reached
    if ((currentPosition >= targetAngle)&&isMoving) {
        isMoving = false;
        Serial.println("Movement complete");
    }
}

void moveStepper(int steps) {
    for (int i = 0; i < steps; i++) {
        stepper.step(1);
        delay(5);
    }
}

long calibrateStepsPerRevolution() {
    //first set home and than counting to reach home again means it completed one revolution if set home again(it circled so it reach the micro switc again)
    //then count the steps and divide by 360 to get the steps per degree
    while(digitalRead(LIMIT_SWITCH_PIN)){
        stepper.step(-1);
        delay(5);
    }
    moveStepper(100);
    long count = 100;
    while(digitalRead(LIMIT_SWITCH_PIN)){
        stepper.step(1);
        delay(5);
        count++;
    }

    return count;
}



void loop() {
    server.handleClient();
    updateMovement();
}


















// #include <Arduino.h>
// #include <ESP8266WiFi.h>
// #include <ESP8266WebServer.h>
// #include <Stepper.h>

// // WiFi settings
// const char* ssid = "StepperControl";
// const char* password = "12345678";

// // Stepper motor pins for ULN2003 driver
// #define IN1 D1
// #define IN2 D2
// #define IN3 D3
// #define IN4 D4
// #define LIMIT_SWITCH_PIN D5  // Limit switch for homing

// // Movement state
// volatile bool isMoving = false;
// volatile bool isHomed = false;
// volatile float currentPosition = 0; // Current position of the stepper motor

// // Steps per revolution for 28BYJ-48 motor
// const int STEPS_PER_REVOLUTION = 111550;  // 32 steps per revolution * 64:1 gearbox
// const float STEPS_PER_DEGREE = 310 ;//STEPS_PER_REVOLUTION / 360.0;

// // Initialize stepper motor
// Stepper stepper(STEPS_PER_REVOLUTION, IN1, IN3, IN2, IN4);
// ESP8266WebServer server(80);

// //function declaration
// void moveStepper(int steps);

// // HTML page with input form
// const char* html = R"rawliteral(
// <!DOCTYPE html>
// <html>
// <head>
//     <title>Antenna Positioning System</title>
//     <style>
//         body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
//         .container { max-width: 600px; margin: 50px auto; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
//         h1 { text-align: center; color: #333; }
//         .input-group { margin: 15px 0; }
//         label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
//         input { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; }
//         button { width: 100%; padding: 10px; font-size: 18px; color: #fff; background-color: #007bff; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; }
//         button.stop { background-color: #ff6b6b; }
//         button:hover { opacity: 0.9; }
//         #status, #current-position { margin: 15px 0; padding: 10px; background-color: #e9ecef; border-radius: 5px; text-align: center; font-size: 18px; }
//     </style>
//     <script>
//         function checkStatus() {
//             fetch('/status')
//                 .then(response => response.json())
//                 .then(data => {
//                     document.getElementById('status').textContent = 'System Status: ' + data.status;
//                     document.getElementById('current-position').textContent = 'Current Position: ' + data.currentAngle.toFixed(2) + '°';
//                 });
//         }

//         function sendCommand(endpoint) {
//             fetch(endpoint).then(() => checkStatus());
//         }

//         function startMovement(event) {
//             event.preventDefault();
//             const formData = new FormData(event.target);
//             const params = new URLSearchParams(formData).toString();
//             fetch('/move?' + params)
//                 .then(() => checkStatus());
//         }

//         setInterval(checkStatus, 1000); // Update status every second
//     </script>
// </head>
// <body>
//     <div class="container">
//         <h1>Antenna Positioning System</h1>
//         <div id="status">System Status: Ready</div>
//         <div id="current-position">Current Position: 0°</div>
//         <button onclick="sendCommand('/home')">Set Zero Position</button>
//         <button onclick="sendCommand('/stop')" class="stop">Emergency Stop</button>
//         <form onsubmit="startMovement(event)">
//             <div class="input-group">
//                 <label for="angle">Target Angle:</label>
//                 <input type="number" id="angle" name="angle" required>
//             </div>
//             <div class="input-group">
//                 <label for="stepSize">Step Size:</label>
//                 <input type="number" id="stepSize" name="stepSize" required>
//             </div>
//             <div class="input-group">
//                 <label for="delay">Delay (seconds):</label>
//                 <input type="number" id="delay" name="delay" required>
//             </div>
//             <button type="submit">Start Mapping</button>
//         </form>
//     </div>
// </body>
// </html>
// )rawliteral";

// // Web server handlers
// void handleRoot() {
//     server.send(200, "text/html", html);
// }

// void handleStatus() {
//     String status = "{";
//     status += "\"status\":\"" + String(isHomed ? (isMoving ? "Moving" : "Ready") : "Not Homed") + "\",";
//     status += "\"currentAngle\":" + String(currentPosition) + "}";
//     server.send(200, "application/json", status);
// }

// void handleStop() {
//     isMoving = false;
//     digitalWrite(IN1, LOW);
//     digitalWrite(IN2, LOW);
//     digitalWrite(IN3, LOW);
//     digitalWrite(IN4, LOW);
//     server.send(200, "text/plain", "Stopped");
// }

// void handleHome() {
//     if (isMoving) {
//         server.send(400, "text/plain", "System is currently moving");
//         return;
//     }

//     isMoving = true;
//     currentPosition = 0;

//     while (digitalRead(LIMIT_SWITCH_PIN) && isMoving) {
//         stepper.step(-1);
//         delay(5);
//     }

//     if (isMoving) {
//         isHomed = true;
//     }

//     isMoving = false;
//     server.send(200, "text/plain", "Homing complete");
// }

// void handleMove() {
//     if (!isHomed) {
//         server.send(400, "text/plain", "Please home the system first");
//         return;
//     }

//     if (isMoving) {
//         server.send(400, "text/plain", "System is currently moving");
//         return;
//     }

//     float targetAngle = server.arg("angle").toFloat();
//     int stepSize = server.arg("stepSize").toInt();
//     //int delayTime = server.arg("delay").toInt() * 1000;// convert to milliseconds
//     unsigned long delayTime = server.arg("delay").toInt() * 1000;

//     if (targetAngle <= 0 || stepSize <= 0 || delayTime < 0) {
//         server.send(400, "text/plain", "Invalid parameters");
//         return;
//     }

//     server.send(200, "text/plain", "Mapping started");
//     isMoving = true;

//     int stepsPerSegment = round(stepSize * STEPS_PER_DEGREE);
//     unsigned long previosTime = 0;
//     unsigned long currentTime = millis();
//     while (currentPosition < targetAngle) {
//         // Check if the elapsed time is greater or equal to the delay time set
//         if (millis() - previosTime >= delayTime) {
//             // Print a message indicating the end of the delay before moving the stepper
//             Serial.printf("End of brake, current position: %d\n", currentPosition);
    
//             // Update the current position and move the stepper motor
//             currentPosition += stepSize;
//             moveStepper(stepsPerSegment);
    
//             // Print a message indicating the start of the delay after moving the stepper
//             Serial.println("start brake");
    
//             // Update the last step time
//             previosTime = millis();
//         }
    
//         // yield() allows background tasks (e.g., WiFi tasks) during the wait
//         yield();
        

//     }
    

//     isMoving = false;
// }

// void setup() {
//     Serial.begin(9600);
//     pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
//     WiFi.softAP(ssid, password);

//     server.on("/", handleRoot);
//     server.on("/move", handleMove);
//     server.on("/home", handleHome);
//     server.on("/stop", handleStop);
//     server.on("/status", handleStatus);

//     server.begin();
//     stepper.setSpeed(10);
//     isHomed = false;
//     isMoving = false;
// }


// void moveStepper(int steps){
//     for(int i = 0; i<steps; i++){
//         stepper.step(1);
//         delay(5);
//     }
// }

// void loop() {
//     server.handleClient();
// }



