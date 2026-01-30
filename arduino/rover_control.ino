// ⚡ Sovereign Arduino Control Script ⚡
// Zachariah's capsule-grade vessel: PWM control, PG pulse RPM tracking
// Extended with BTS7960 actuator subsystem + Optocoupler F/R control
// Now with structured telemetry for host pipeline

const int pwmPin = 6;   // Dedicated PWM output pin

// PG signal tracking
volatile unsigned long lastPulseMicros = 0;
volatile unsigned long pulseIntervalMicros = 0;
float rpm = 0.0;
const int motorPoles = 4;
unsigned long lastUpdateMillis = 0;

// BTS7960 pins
const int RPWM = 7;
const int LPWM = 8;
const int R_EN = 22;
const int L_EN = 23;

// Optocoupler F/R control pin
const int FR_CTRL = 24;   // Drives optocoupler → WS55-220 F/R input

// --- Telemetry state ---
int currentPwm = 0;          // PWM output (0–255)
int currentActSpeed = 0;     // BTS7960 actuator speed (0–255)
String currentDir = "STOP";  // "FWD", "REV", "STOP"

// --- Telemetry timing ---
unsigned long lastTelemetryMillis = 0;
const unsigned long telemetryInterval = 500;  // ms

void onPGPulse() {
  unsigned long now = micros();
  pulseIntervalMicros = now - lastPulseMicros;
  lastPulseMicros = now;
  lastUpdateMillis = millis();
}

void setup() {
  Serial.begin(9600);
  Serial.println("⚡ Sovereign Capsule Booting...");

  // PWM pin setup
  pinMode(pwmPin, OUTPUT);
  analogWrite(pwmPin, 0);
  Serial.println("PWM subsystem initialized.");

  // PG input setup
  pinMode(2, INPUT);
  attachInterrupt(digitalPinToInterrupt(2), onPGPulse, RISING);
  Serial.println("PG telemetry subsystem armed.");

  // BTS7960 setup
  pinMode(RPWM, OUTPUT);
  pinMode(LPWM, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_EN, OUTPUT);

  digitalWrite(R_EN, HIGH);
  digitalWrite(L_EN, HIGH);
  analogWrite(RPWM, 0);
  analogWrite(LPWM, 0);
  Serial.println("Actuator subsystem enabled.");

  // Optocoupler F/R setup
  pinMode(FR_CTRL, OUTPUT);
  digitalWrite(FR_CTRL, LOW);  // Default forward
  Serial.println("Optocoupler F/R control initialized.");
}

void loop() {
  // 🔹 Serial command parser
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    Serial.print("CMD Received: ");
    Serial.println(input);

    // --- Actuator control ---
    if (input.startsWith("ACT:FWD:")) {
      int speed = input.substring(8).toInt();
      speed = constrain(speed, 0, 255);
      analogWrite(RPWM, speed);
      analogWrite(LPWM, 0);
      currentActSpeed = speed;
      Serial.print("ACK:ACT:FWD:");
      Serial.println(speed);
    }
    else if (input.startsWith("ACT:REV:")) {
      int speed = input.substring(8).toInt();
      speed = constrain(speed, 0, 255);
      analogWrite(LPWM, speed);
      analogWrite(RPWM, 0);
      currentActSpeed = speed;
      Serial.print("ACK:ACT:REV:");
      Serial.println(speed);
    }
    else if (input.startsWith("ACT:STOP")) {
      analogWrite(RPWM, 0);
      analogWrite(LPWM, 0);
      currentActSpeed = 0;
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

    // --- Direction control (optocoupler) ---
    else if (input.startsWith("DIR:FWD")) {
      digitalWrite(FR_CTRL, LOW);
      currentDir = "FWD";   // Always reflect commanded direction
      Serial.println("ACK:DIR:FWD");
    }
    else if (input.startsWith("DIR:REV")) {
      digitalWrite(FR_CTRL, HIGH);
      currentDir = "REV";   // Always reflect commanded direction
      Serial.println("ACK:DIR:REV");
    }

    // --- System-wide STOP ---
    else if (input.startsWith("SYS:STOP")) {
      analogWrite(RPWM, 0);
      analogWrite(LPWM, 0);
      analogWrite(pwmPin, 0);

      digitalWrite(FR_CTRL, LOW);  // Safe default

      currentActSpeed = 0;
      currentPwm = 0;
      currentDir = "STOP";
      rpm = 0.0;

      Serial.println("ACK:SYS:STOP");
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
    rpm = 0.0;
  }

  // 🔸 Structured telemetry output every 500 ms
  if (now - lastTelemetryMillis >= telemetryInterval) {
    lastTelemetryMillis = now;

    float throttle = currentActSpeed / 255.0;

    Serial.print("TEL:RPM:");
    Serial.print(rpm, 1);

    Serial.print(" THR:");
    Serial.print(throttle, 2);

    Serial.print(" DIR:");
    Serial.print(currentDir);

    Serial.print(" PWM:");
    Serial.println(currentPwm);
  }
}
