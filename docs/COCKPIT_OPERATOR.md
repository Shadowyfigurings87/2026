# Rover1 Cockpit — Operator Sheet

## Primary Telemetry Panel

**Fields:**

- **RPM**  
  - Live wheel/motor speed.  
  - Source: `arduino_state.rpm`.

- **Throttle**  
  - 0.0–1.0 normalized throttle.  
  - Source: `arduino_state.throttle`.

- **Direction**  
  - `STOP`, `FWD`, `REV`.  
  - Source: `arduino_state.direction`.

- **PWM**  
  - Raw PWM duty value.  
  - Source: `arduino_state.pwm`.

- **Voltage / Temp**  
  - Reserved for future firmware expansion.

---

## Health & Status

- **Heartbeat**  
  - Synthetic system heartbeat from `heartbeat_stream()`.  
  - Confirms ingestion loop is alive.

- **Watchdog**  
  - `watchdog_stream()` events indicate internal health checks.  
  - Used to detect stalls or dead loops.

- **Arduino Metrics**  
  - `ministry_metrics` frames from Arduino ministry.  
  - Includes bytes read, lines read, reconnect count, last error.

---

## Command Loop (Mental Model)

1. You click a control in the cockpit.  
2. UI sends JSON command to Host API.  
3. Host TCP server writes JSONL down tunnel.  
4. Rover uplink `_command_listener()` receives it.  
5. `handle_command_packet()` translates to Arduino command string.  
6. `write_to_arduino()` sends it over serial.  
7. Arduino executes motion and emits `ACK` + `TEL`.  
8. Telemetry returns to the cockpit, closing the loop.

---

## Operator Checklist

- **Before motion:**
  - Confirm telemetry is updating (RPM, throttle, direction).  
  - Confirm heartbeat events are present.  
  - Confirm Arduino metrics show no recent errors.

- **During motion:**
  - Watch RPM vs throttle for anomalies.  
  - Watch direction matches intended command.  
  - Watch for stalled telemetry or missing heartbeats.

- **After motion:**
  - Confirm rover returns to `STOP`.  
  - Confirm telemetry stabilizes at RPM 0, throttle 0.  
  - Log any anomalies in the lineage archive.
