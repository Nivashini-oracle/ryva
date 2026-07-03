#include <Wire.h>
#include <MPU6050.h>
#include <DHT.h>
MPU6050 mpu;
DHT dht(2, DHT22);  // change pin 2 if your DHT22 is on different pin
unsigned long lastDHTRead = 0;
unsigned long lastVibCheck = 0;
unsigned long lastPrint = 0;
const int BUF_SIZE = 50;
float ax_buf[BUF_SIZE], ay_buf[BUF_SIZE], az_buf[BUF_SIZE];
int buf_idx = 0;
bool buf_full = false;
bool vib_flag = false;
const float VIB_THRESHOLD = 0.3;
float lastTemp = 0;
float lastHum = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  mpu.initialize();
  dht.begin();
  if (mpu.testConnection()) {
    Serial.println("MPU6050 OK");
  } else {
    Serial.println("MPU6050 FAILED - check wiring");
  }
}

float calculateVariance(float buf[], int size) {
  float sum = 0;
  for (int i = 0; i < size; i++) sum += buf[i];
  float mean = sum / size;
  float sqDiffSum = 0;
  for (int i = 0; i < size; i++) sqDiffSum += (buf[i] - mean) * (buf[i] - mean);
  return sqDiffSum / size;
}

void checkVibration() {
  float mx = 0, my = 0, mz = 0;
  for (int i = 0; i < 25; i++) {
    int idx = (buf_idx - 1 - i + BUF_SIZE) % BUF_SIZE;
    mx += ax_buf[idx];
    my += ay_buf[idx];
    mz += az_buf[idx];
  }
  mx /= 25.0;
  my /= 25.0;
  mz /= 25.0;

  float sumSq = 0;
  for (int i = 0; i < 25; i++) {
    int idx = (buf_idx - 1 - i + BUF_SIZE) % BUF_SIZE;
    float dx = ax_buf[idx] - mx;
    float dy = ay_buf[idx] - my;
    float dz = az_buf[idx] - mz;
    sumSq += dx*dx + dy*dy + dz*dz;
  }

  float vib_rms = sqrt(sumSq / 25.0);
  vib_flag = (vib_rms > VIB_THRESHOLD);
}

void loop() {
  int16_t ax_raw, ay_raw, az_raw;
  mpu.getAcceleration(&ax_raw, &ay_raw, &az_raw);

  float ax_g = ax_raw / 16384.0;
  float ay_g = ay_raw / 16384.0;
  float az_g = az_raw / 16384.0;

  ax_buf[buf_idx] = ax_g;
  ay_buf[buf_idx] = ay_g;
  az_buf[buf_idx] = az_g;
  buf_idx = (buf_idx + 1) % BUF_SIZE;
  if (buf_idx == 0) buf_full = true;

  float variance = 0;
  if (buf_full) {
    variance = calculateVariance(ax_buf, BUF_SIZE)
             + calculateVariance(ay_buf, BUF_SIZE)
             + calculateVariance(az_buf, BUF_SIZE);
  }

  if (buf_full && millis() - lastVibCheck > 500) {
    checkVibration();
    lastVibCheck = millis();
  }

  if (millis() - lastDHTRead > 5000) {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      lastTemp = t;
      lastHum = h;
    } else {
      Serial.println("DHT22 read failed - check wiring");
    }
    lastDHTRead = millis();
  }

  if (millis() - lastPrint >= 1000) {
    Serial.print("MPU:");
    Serial.print(ax_g, 3); Serial.print(",");
    Serial.print(ay_g, 3); Serial.print(",");
    Serial.print(az_g, 3);
    Serial.print("|TEMP:"); Serial.print(lastTemp, 1);
    Serial.print("|HUM:");  Serial.print(lastHum, 1);
    Serial.print("|VAR:");  Serial.print(variance, 4);
    Serial.print("|VIB:");  Serial.println(vib_flag ? "1" : "0");
    lastPrint = millis();
  }

  delay(20);
}