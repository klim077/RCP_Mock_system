import 'package:flutter/material.dart';
import 'text.dart';

class SmartGymButtons {
  Widget stopRecordingButton(Function onpress) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[
            Colors.orange[600],
            Colors.red[600],
          ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 65,
      width: 250,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Flexible(
              flex: 2,
              child: Icon(
                Icons.stop_circle_outlined,
                size: 35,
              ),
            ),
            Flexible(flex: 1, child: Container()),
            Flexible(
              flex: 12,
              child: Text(
                'End Session'.toUpperCase(),
                style: TextStyle(
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget largeIconButton({Function onpress, IconData icon, String text}) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[
            Colors.orange[600],
            Colors.red[600],
          ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 60,
      width: 350,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Flexible(
              flex: 2,
              child: Icon(
                icon,
                size: 35,
              ),
            ),
            Flexible(flex: 1, child: Container()),
            Flexible(
              flex: 12,
              child: Text(
                text.toUpperCase(),
                style: TextStyle(
                  fontSize: 15,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget smallRectangleButton({Function onpress, String text, bool color}) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: color
              ? <Color>[
                  Colors.orange[600],
                  Colors.red[600],
                ]
              : <Color>[
                  Colors.grey[300],
                  Colors.grey[300],
                ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(5.0)),
      ),
      height: 30,
      width: 200,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Text(
          text.toUpperCase(),
          style: TextStyle(
            fontSize: 12,
            color: color ? Colors.white : Colors.black,
          ),
        ),
      ),
    );
  }

  Widget mediumIconButton({Function onpress, IconData icon, String text}) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[
            Colors.orange[600],
            Colors.red[600],
          ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 60,
      width: 260,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Flexible(
              flex: 2,
              child: Icon(
                icon,
                size: 32,
              ),
            ),
            Flexible(flex: 1, child: Container()),
            Flexible(
              flex: 12,
              child: Text(
                text.toUpperCase(),
                style: TextStyle(
                  fontSize: 14,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget smallButton(Function onpress, String text, bool color) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: color
              ? <Color>[
                  Colors.orange[600],
                  Colors.red[600],
                ]
              : <Color>[
                  Colors.grey[300],
                  Colors.grey[300],
                ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 60,
      width: 180,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Text(
          text.toUpperCase(),
          style: TextStyle(
            fontSize: 14,
            color: color ? Colors.white : Colors.black,
          ),
        ),
      ),
    );
  }

  Widget mediumButton({Function onpress, String text, bool color}) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: color
              ? <Color>[
                  Colors.orange[600],
                  Colors.red[600],
                ]
              : <Color>[
                  Colors.grey[300],
                  Colors.grey[300],
                ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 60,
      width: 260,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Text(
          text.toUpperCase(),
          style: TextStyle(
            fontSize: 15,
            color: color ? Colors.white : Colors.black,
          ),
        ),
      ),
    );
  }

  Widget textButton(Function onpress, String text) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(4),
      )),
      child: Padding(
        padding: const EdgeInsets.all(10.0),
        child: CustomText().whiteButtonText(text),
      ),
      onPressed: () => [onpress()],
    );
  }

  Widget retakeWeightButton(Function onpress, {bool isDisabled = false}) {
    return isDisabled
        ? Container()
        : ElevatedButton(
            style: ElevatedButton.styleFrom(
                shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4),
            )),
            child: Padding(
              padding: const EdgeInsets.all(10.0),
              child: CustomText().whiteButtonText('Retake'),
            ),
            onPressed: () => [onpress()],
          );
  }

  Widget stopRecordingButtonSmall(Function onpress) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(4),
      )),
      child: Padding(
        padding: const EdgeInsets.all(10.0),
        child: CustomText().whiteButtonText('Stop \nRecording'),
      ),
      onPressed: () => [onpress()],
    );
  }

  Widget tinyButton(Function onpress, String text, bool color) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: color
              ? <Color>[
                  Colors.red[300],
                  Colors.red[600],
                ]
              : <Color>[
                  Colors.grey[300],
                  Colors.grey[300],
                ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: 30,
      width: 100,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Text(
          text.toUpperCase(),
          style: TextStyle(
            fontSize: 12,
            color: color ? Colors.white : Colors.black,
          ),
        ),
      ),
    );
  }

  //new custom icon button to set width,height,fontsize,iconsize with initialized values
  Widget customIconButton(
      {Function onpress,
      IconData icon,
      String text,
      double height = 60,
      double width = 260,
      double fontSize = 14,
      double iconSize = 32}) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[
            Colors.orange[600],
            Colors.red[600],
          ],
        ),
        borderRadius: BorderRadius.all(Radius.circular(50.0)),
      ),
      height: height,
      width: width,
      child: TextButton(
        style: TextButton.styleFrom(primary: Colors.white),
        onPressed: () => [onpress()],
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Flexible(
              flex: 2,
              child: Icon(
                icon,
                size: iconSize,
              ),
            ),
            Flexible(flex: 2, child: Container()),
            Flexible(
              flex: 12,
              child: Text(
                text.toUpperCase(),
                style: TextStyle(
                  fontSize: fontSize,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
