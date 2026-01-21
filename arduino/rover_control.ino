// ⚡ Sovereign Arduino Control Script ⚡
// Zachariah's capsule-grade vessel: PWM control, PG pulse RPM tracking
// Extended with BTS7960 actuator subsystem + Optocoupler F/R control
// Now with structured telemetry for host pipeline

const int pwmPin = 6;   // Dedicated PWM output pin

// PG signal tracking
volatile unsigned long lastPulseMicros = 0;
volatile unsigned long pulseIntervalMicros = 0;
float rpm = 0.0;
const int motorPoles = 4;  // Adjust to match your motor
unsigned long lastUpdateMillis = 0;

// BTS7960 pins
const int RPWM = 7;
const int LPWM = 8;
const int R_EN = 22;
const int L_EN = 23;

// Optocoupler F/R control pin
const int FR_CTRL = 24;   // Drives optocoupler → WS55-220 F/R input

// --- Telemetry state ---
int currentPwm = 0;          // Raw PWM on pwmPin (0–255)
int currentActSpeed = 0;     // BTS7960 speed (0–255)
String currentDir = "STOP";  // "FWD", "REV", "STOP"

// --- Telemetry timing ---
unsigned long lastTelemetryMillis = 0;
const unsigned long telemetryInterval = 500;  // ms

void onPGPulse() {
  unsigned long now = micros();
  pulseIntervalMicros = now - lastPulseMicros;
  lastPulseMicros = now;
  lastUpdateMillis = millis();  // Refresh timestamp only when a pulse arrives
}

void setup() {
  Serial.begin(9600);
  Serial.println("⚡ Sovereign Capsule Booting...");

  // PWM pin setup
  pinMode(pwmPin, OUTPUT);
  analogWrite(pwmPin, 0);  // Start with 0 duty cycle
  Serial.println("PWM subsystem initialized.");

  // PG input setup
  pinMode(2, INPUT);  // PG signal from WS55-220
  attachInterrupt(digitalPinToInterrupt(2), onPGPulse, RISING);
  Serial.println("PG telemetry subsystem armed.");

  // BTS7960 setup
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);

  digitalWrite(R_EN, HIGH);  // Enable right channel
  digitalWrite(L_EN, HIGH);  // Enable left channel
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
  Serial.println("Actuator subsystem enabled (EN pins HIGH).");

  // Optocoupler F/R setup
  pinMode(FR_CTRL, OUTPUT);
  digitalWrite(FR_CTRL, LOW);  // Default forward (not grounding F/R)
  Serial.println("Optocoupler F/R control initialized.");
}

void loop() {
  // 🔹 Serial command parser
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Remove whitespace/newlines

    Serial.print("CMD Received: ");
    Serial.println(input);

    // --- Actuator control ---
    if (input.startsWith("ACT:FWD:")) {
      int speed = input.substring(8).toInt();
      speed = constrain(speed, 0, 255);
      analogWrite(RPWM, speed);
      analogWrite(LPWM, 0);  // safety: only one channel active
      currentActSpeed = speed;
      currentDir = (speed > 0) ? "FWD" : "STOP";
      Serial.print("ACK:ACT:FWD:");
      Serial.println(speed);
    }
    else if (input.startsWith("ACT:REV:")) {
      int speed = input.substring(8).toInt();
      speed = constrain(speed, 0, 255);
      analogWrite(LPWM, speed);
      analogWrite(RPWM, 0);  // safety: only one channel active
      currentActSpeed = speed;
      currentDir = (speed > 0) ? "REV" : "STOP";
      Serial.print("ACK:ACT:REV:");
      Serial.println(speed);
    }
    else if (input.startsWith("ACT:STOP")) {
      analogWrite(RPWM, 0);
      analogWrite(LPWM, 0);
      currentActSpeed = 0;
      currentDir = "STOP";
      Serial.println("ACK:ACT:STOP");
    }
    // --- PWM control ---
    else if (input.startsWith("PWM:")) {
      int pwmValue = input.substring(4).toInt();
      pwmValue = constrain(pwmValue, 0, 255);
      analogWrite(pwmPin, pwmValue);
      currentPwm = pwmValue;
      Serial.print("ACK:PWM:");
      Serial.println(pwmValue);
    }
    // --- Direction control via optocoupler ---
    else if (input.startsWith("DIR:FWD")) {
      digitalWrite(FR_CTRL, LOW);  // Forward (F/R not grounded)
      currentDir = (currentActSpeed > 0) ? "FWD" : "STOP";
      Serial.println("ACK:DIR:FWD");
    }
    else if (input.startsWith("DIR:REV")) {
      digitalWrite(FR_CTRL, HIGH); // Reverse (F/R grounded via optocoupler)
      currentDir = (currentActSpeed > 0) ? "REV" : "STOP";
      Serial.println("ACK:DIR:REV");
    }
    else {
      Serial.println("ERR:Unknown command");
    }
  }

  // 🔸 PG signal RPM calculation with timeout
  unsigned long now = millis();

  if (pulseIntervalMicros > 0) {
    float freq = 1e6 / pulseIntervalMicros;
    rpm = (freq * 60) / (2 * motorPoles);
  }

  if (now - lastUpdateMillis > 1000) {
    rpm = 0.0;  // Timeout → motor stopped
  }

  // 🔸 Structured telemetry output every 500 ms
  if (now - lastTelemetryMillis >= telemetryInterval) {
    lastTelemetryMillis = now;

    // Throttle as 0–1 based on actuator speed (you can change this mapping later)
    float throttle = currentActSpeed / 255.0;

    Serial.print("TEL:RPM:");
    Serial.print(rpm, 1);  // one decimal place

    Serial.print(" THR:");
    Serial.print(throttle, 2);

    Serial.print(" DIR:");
    Serial.print(currentDir);

    Serial.print(" PWM:");
    Serial.println(currentPwm);
    // Future: add VOLT: / TEMP: here when sensors exist
  }
}
