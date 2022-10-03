import 'package:flutter/material.dart';

class CustomText {
  Widget title(String text, {Color color = Colors.black}) {
    return Text(
      text,
      style:
          TextStyle(fontSize: 20.0, fontWeight: FontWeight.bold, color: color),
    );
  }

  Widget subHeader(String text) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 20.0,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget paragraph(String text) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 20.0,
        fontWeight: FontWeight.normal,
      ),
      textAlign: TextAlign.justify,
    );
  }

  Widget header(String text, {Color color}) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 20.0,
        fontWeight: FontWeight.bold,
        color: color,
      ),
    );
  }

  Widget body(String text, {Color color}) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 14.0,
        fontWeight: FontWeight.bold,
        color: color,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget workoutDetails(String text) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 12.0,
      ),
    );
  }

  Widget buttonText(String text) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 20.0,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget whiteButtonText(String text) {
    return Text(
      text,
      textAlign: TextAlign.center,
      style: TextStyle(
        color: Colors.white,
        fontSize: 15.0,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget infoText(String text, {Color color, double fontSize = 20}) {
    return Text(
      text,
      style: TextStyle(
        fontSize: fontSize,
        fontWeight: FontWeight.normal,
        color: color,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget smallInfoText(String text, {Color color}) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 12.0,
        fontWeight: FontWeight.normal,
        color: color,
      ),
    );
  }
}

class ConstantText {
  static const speedUnit = 'Km/h';
  static const timeUnit = 'hh:mm:ss';
  static const caloriesUnit = 'Cals';
  static const minutesUnit = 'Mins';
  static const errorPopUpInvalidQRCode =
      'Invalid or expired QR code,\nPlease start a workout before checking your workout history\n';
  static const errorPopUpExpiredQRCode =
      'Invalid or expired QR code,\nPlease refresh QR code and try again\n';
  static const distanceSIUnt = 'Km';
  static const scanActiveSGQr = 'Scan ActiveSG QR';
  static const inclinationAngle = 'degrees';
  static const percent = 'percent';
  static const milesperhour = 'miles/h';
  static const mile = 'miles';
  static const meters = 'm';
  static const altitudeClimb = 'Altitude Climbed';
  static const avgPace = 'Avg Pace';
  static const powerUnit = 'Watts';
  static const cadenceUnit = 'Rpm';
}

final textColor = Colors.grey[600];
