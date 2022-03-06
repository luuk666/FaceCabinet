
int i;
byte comdata[20];

void setup() {
  Serial.begin(115200);
  pinMode(12, OUTPUT);
  digitalWrite(12, HIGH);
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
}

void loop()
{


  USART_RE();
}


void open_door(int id)
{
  if (id == 0)
  {
    Serial.print("strat");
    digitalWrite(13, LOW);
    delay(1000);
    digitalWrite(13, HIGH);
     Serial.print("end");
  }

  if (id == 1)
  {
    Serial.print("strat");
    digitalWrite(12, LOW);
    delay(1000);
    digitalWrite(12, HIGH);
     Serial.print("end");
  }

}

void USART_RE()
{
  while (Serial.available() > 0)
  {
    delay(3);
    i++;//接收一个字节加1
    comdata[i - 1] = Serial.read();
    Serial.print(i - 1);      Serial.print("=");    Serial.println(comdata[i - 1]);

    if (comdata[0] != 0xA1)
    {
      i = 0;
      for (int k  = 0; k < 20; k++)
      {
        comdata[k] = 0;
      }
    }

    if (  i >= 3)
    {

      if (comdata[0] == 0xA1 &&
          comdata[1] == 0xA2
         )
      {

        open_door(comdata[2]);

      }
      else
      {
        Serial.print("error!");

      }
      i = 0;
      for (int k  = 0; k < 20; k++)
      {
        comdata[k] = 0;
      }
    }
  }
}