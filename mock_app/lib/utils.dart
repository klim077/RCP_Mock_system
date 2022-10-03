import 'package:socket_io_client/socket_io_client.dart' as sio;

import 'config.dart';
import 'package:socket_io_client/socket_io_client.dart';

class Utils {
  static final Utils _singleton = Utils._internal();

  factory Utils() => _singleton;

  Utils._internal();

  static Socket socket = sio.io(backendURL, {
    'path': '/socket.io/',
    // 'secure': true,
    'autoConnect': false,
    // 'reconnectionAttempts': 1,
    'transports': ['websocket']
  });

  

  String? capitalize(String input) {
    if (input == null) {
      return null;
    }

    if (input.length == 1) {
      return input.toUpperCase();
    }

    return input[0].toUpperCase() + input.substring(1);
  }

  String getWorkoutDurationInTimeFormat(double totalDuration) {
    if (!totalDuration.isInfinite && !totalDuration.isNaN) {
      final String hoursStr = ((totalDuration / 60) / 60).floor().toString();

      final String minutesStr =
          ((totalDuration / 60) % 60).floor().toString().padLeft(2, '0');
      final String secondsStr =
          (totalDuration % 60).floor().toString().padLeft(2, '0');
      if (((totalDuration / 60) / 60).floor() < 1) {
        return '0:$minutesStr:$secondsStr';
      }
      return '$hoursStr:$minutesStr:$secondsStr';
    } else {
      return '-';
    }
  }

  String maskPhoneNumber(String phoneNo) {
    return ("xxxxx" + phoneNo.substring(5));
  }

  static double convertToDouble(var input) {
    try {
      return (input.toDouble());
    } catch (err) {
      throw FormatException("cannot convert to double");
    }
  }

  String enumToString(Object o) => o.toString().split('.').last;

  // T enumFromString<T>(String key, List<T> values) =>
  //     values.firstWhere((v) => key == enumToString(v!), orElse: () => null);
}
