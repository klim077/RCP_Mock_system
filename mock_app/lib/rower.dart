import 'package:meta/meta.dart';

class Rower {
  final String machineId;
  final String userId;
  final String machineLocation;
  final String machineName;
  String exerciseGroup;
  double distance; // meters
  double cadence;
  double calories; // kilo joules
  double pace;
  double power; // watts
  double strokes;
  double timestamp;
  double workoutTime;
  bool rec;

  Rower(
      {@required this.machineId,
      @required this.userId,
      @required this.machineLocation,
      @required this.machineName,
      @required this.exerciseGroup,
      this.distance,
      this.cadence,
      this.calories,
      this.pace,
      this.power,
      this.strokes,
      this.timestamp,
      this.workoutTime,
      this.rec})
      : assert(machineId != null);

  String toString() {
    Map<String, dynamic> out = {
      'machineId': machineId,
      'machineName': machineName,
      'machineLocation': machineLocation,
      'userId': userId,
      'cadence': cadence,
      'distance': distance,
      'calories': calories,
      'exerciseGroup': exerciseGroup,
      'power': power,
      'pace': pace,
      'strokes': strokes,
      'timestamp': timestamp,
      'workoutTime': workoutTime,
      'rec': rec
    };
    return out.toString();
  }
}
