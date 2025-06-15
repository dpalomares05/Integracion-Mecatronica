const int sensorPin = A0;

void setup() {
  Serial.begin(115200); // Alta velocidad para buena resolución temporal
}

void loop() {
  int valor = analogRead(sensorPin); // Valor de 0 a 1023
  Serial.println(valor);             // Envío por puerto serial
  delayMicroseconds(200);           
}
