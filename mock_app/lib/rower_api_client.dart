import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:myapp/models/models.dart';
import 'package:myapp/repositories/openapi_client.dart';

import 'package:myapp/common/Functions/utils.dart';

import 'package:logger/logger.dart';
import 'package:path_provider/path_provider.dart';

import 'package:myapp/repositories/common.dart';

class StaticBikeApiClient {
  OpenApiClient openApiClient;

  StreamController<StaticBike> ctrl;
  StreamController<PostReplyEnum> postReply;

  String _userId;

  bool socketStatus = false;

  var logger;

  StaticBikeApiClient() {
    print("StaticBikeInit");
    _init();
  }

  void _init() async {
    openApiClient = OpenApiClient.jwt();

    Directory appDocDir = await getExternalStorageDirectory();
    String appDocPath = appDocDir.path;
    print(appDocDir);

    logger = Logger(
        printer: PrettyPrinter(),
        output: FileOutput(
            file: new File(appDocPath + '/static_bike_api_client.txt')));
  }

  Stream<PostReplyEnum> fetchPostReplyStream(String userId) {
    // Create a local stream controller
    postReply = StreamController<PostReplyEnum>();
    print('getting stream');

    var channel = '{ "channel" : "' + userId + '" }';

    print('channel $channel');

    Utils.socket.emit('mobileConnected', channel);

    return postReply.stream;
  }

  void unsubscribePostReplyStream(String userId) {
    postReply.close();
  }

  void connect2SocketIO(String machineId) async {
    logger.d('static bike calling socket connect!');
    Utils.setServer();
    Utils.socket.connect();

    final String endpoint = '/machines/$machineId/keyvalues';
    final response = await openApiClient.get(endpoint);
    var res = json.decode(response.body);
    print(res.toString());
    // TelegramAlert().setup(
    // machineName: res['name'] + '@' + res['location'], machineId: machineId);

    // TelegramAlert().start();

    Utils.socket.on('connect', (_) {
      socketStatus = true;

      var channel = '{ "channel" : "' + _userId + '" }';
      Utils.socket.emit('mobileConnected', channel);

      logger.d('this static bike socket id: ' + Utils.socket.id);
      print('*********************************************************');
      print('Socket Connected ');
      print('*********************************************************');
    });

    Utils.socket.on('ackmessage',
        (data) => logger.d("Static Bike ack message from server: " + data));

    // this socket.io updatemessage will replace _handleEvent(event)
    Utils.socket.on('updatemessage', (data) async {
      // print("Received update from server:  " + data);
      print('*********************************************************');
      print("socket updatemessage" + data);
      print('*********************************************************');
      try {
        logger.d(
            '[Static Bike ${Utils.socket.id}] received update from server: $data');

        if (data is String) {
          // Parse machineId
          data = json.decode(data);
          String machineId = data["machine_id"];
          print("data:");

          // Get the rep count based on event message
          //String repStr = await redisCommand.get(event.message);
          logger.d('Server getting workout metrics: ');
          print('Server getting workout metrics: ');

          final String endpoint = '/machines/$machineId/keyvalues';
          final response = await openApiClient.get(endpoint);

          print('endpoint: $endpoint');

          logger.d('Response status: ${response.statusCode}');
          logger.d('Response body: ${response.body}');
          print('Response body: ${response.body}');

          var res = json.decode(response.body);
          print('res: $res');

          print('res: $res');

          // Get machine location
          String machineLocation = res['location'];
          print('location: $machineLocation');

          // Get machine name
          String machineName = res['name'];
          print('machine name; $machineName');

          // Construct a key for the distance
          double distanceDouble = res['distance'];
          print('distance: $distanceDouble');

          // Construct a key for the workoutTime
          double workoutTimeDouble = res['workoutTime']; // to remove]
          print('workout time: $workoutTimeDouble');

          // Construct a key for the calories
          double caloriesDouble = res['calories'];
          print('calories: $caloriesDouble');

          //Construct a key for the power
          double powerDouble = res['power'];
          print('power: $powerDouble');

          //Construct a key for the power
          double cadenceDouble = res['cadence'];
          print('cadence: $cadenceDouble');

          //Construct a key for the speed
          double speedDouble = res['speed'];
          print('speed $speedDouble');

          // Construct a key for the avgSpeed
          double avgSpeedDouble = res['avgSpeed'];
          print('avg_speed: $avgSpeedDouble');

          // Construct a key for the avgCadence
          double avgCadenceDouble = res['avgCadence'];
          print('avg_cadence: $avgCadenceDouble');

          String exerciseGroup = res['exercise_group'];

// Construct StaticBike object
          StaticBike staticBike = StaticBike(
              machineLocation: machineLocation,
              machineName: machineName,
              userId: _userId,
              machineId: machineId,
              speed: speedDouble,
              cadence: cadenceDouble,
              distance: distanceDouble,
              calories: caloriesDouble,
              power: powerDouble,
              exerciseGroup: exerciseGroup,
              currentAvgSpeed: avgSpeedDouble,
              currentAvgCadence: avgCadenceDouble,
              workoutTime: workoutTimeDouble);

          // Put on stream
          if (!ctrl.isClosed) {
            ctrl.sink.add(staticBike);
          }

          // TelegramAlert().reset();
        }

        if (data is String && data.toLowerCase().contains('posted')) {
          if (!postReply.isClosed) {
            logger.d('static bike received posted');
            postReply.sink.add(PostReplyEnum.Posted);
          }
        }
      } catch (err) {}
    });

    Utils.socket.on('disconnect', (_) {
      socketStatus = false;
      logger.d('Static Bike socket.io disconnect: ${Utils.socket.id}');
      print('*********************************************************');
      print('Socket disconnected ');
      print('*********************************************************');
      // TelegramAlert().stop();
    });

    Utils.socket.on('reconnect', (_) {
      print('*********************************************************');
      print("socket reconnect");
      print('*********************************************************');
    });

    Utils.socket.on('reconnect_failed', (_) {
      print('*********************************************************');
      print("socket reconnect_failed");
      print('*********************************************************');
    });

    Utils.socket.on('reconnecting', (_) {
      print('*********************************************************');
      print("socket reconnecting");
      print('*********************************************************');
    });
    //print('Socket connected? ' + this.socket.connected.toString());
  }

  void disconnectSocketIO() async {
    print('calling socket disconnect!');
    Utils.socket.disconnect();
    print(Utils.socket.hasListeners("connect"));
    Utils.socket.clearListeners();
    print(Utils.socket.hasListeners("connect"));
    Utils.socket.close();

    print('Socket connected? ' + Utils.socket.connected.toString());
  }

  Future<void> postExerciseMongoApiCall(String machineId) async {
    // print(mongoUrl);
    // final query = '$mongoApiUrl/machines/$machineId/dispatch';

    final String endpoint = '/machines/$machineId/dispatch';
    //final OpenApiClient openApiClient = OpenApiClient.jwt();
    final response = await openApiClient.post(endpoint);

    // Guard for bad response
    if (response.statusCode != 202) {
      throw Exception('Error dispatching for $machineId');
    }

    print("Response ${response.statusCode}: ${response.body}");
  }

  void initializeWithUser(String machineId, String user) async {
    var body = {'value': user};

    final String endpoint = '/machines/$machineId/initializeStaticbikeWithUser';
    final response = await openApiClient.post(endpoint, body: body);

    logger.d('Response status - initializeWithUser: ${response.statusCode}');
    logger.d('Response body - initializeWithUser: ${response.body}');
  }

  Future<String> getRecordingFlag(String machineId) async {
    // String key = '$machineId:rec';
    // return await redisCommand.get(key);
    try {
      final String endpoint = '/machines/$machineId/keyvalues';
      final response = await openApiClient.get(endpoint);

      logger.d('Response status - getRecordingFlag: ${response.statusCode}');
      logger.d('Response body - getRecordingFlag: ${response.body}');

      var res = json.decode(response.body);
      logger.d(res['rec'].toString());
      return res['rec'].toString();
    } catch (err) {
      return 'false';
    }
  }

  Future<String> getCadence(String machineId) async {
    try {
      final String endpoint = '/machines/$machineId/keyvalues';
      final response = await openApiClient.get(endpoint);

      logger.d('Response status - getRecordingFlag: ${response.statusCode}');
      logger.d('Response body - getRecordingFlag: ${response.body}');

      var res = json.decode(response.body);
      logger.d(res['cadence'].tonum());
      return res['cadence'].tonum();
    } catch (err) {
      return '0';
    }
  }

  void clearUser(String machineId, String user) async {
    // final String key = '$machine:user';
    // print(key);
    // await redisCommand.del(key: key);

    final String endpoint = '/machines/$machineId/keyvalues/user';
    final response = await openApiClient.delete(endpoint);

    logger.d('Response status - clearUser: ${response.statusCode}');
    logger.d('Response body - clearUser: ${response.body}');
  }

  void setUser(String machine, String user) async {
    // final String key = '$machine:user';
    // print(key);
    // await redisCommand.set(key, user);
    var body = {'value': user};

    final String endpoint = '/machines/$machine/keyvalues/user';
    final response = await openApiClient.post(endpoint, body: body);

    logger.d('Response status - setUser: ${response.statusCode}');
    logger.d('Response body - setUser: ${response.body}');
  }

  Future<String> getMachineName(String machineId) async {
    // String key = '$machineId:name';
    // return await redisCommand.get(key);

    final String endpoint = '/machines/$machineId/keyvalues';
    final response = await openApiClient.get(endpoint);

    logger.d('Response status - getMachineName: ${response.statusCode}');
    logger.d('Response body - getMachineName: ${response.body}');

    var res = json.decode(response.body);
    print(res['name']);
    return res['name'];
  }

  String getMachineId(String input) {
    List<String> result = input.split(':');
    // Return first string
    return result[0];
  }

  Future<String> getMachineLocation(String machineId) async {
    // String key = '$machineId:location';
    // return await redisCommand.get(key);

    final String endpoint = '/machines/$machineId/keyvalues';
    final response = await openApiClient.get(endpoint);

    logger.d('Response status - getMachineLocation: ${response.statusCode}');
    logger.d('Response body - getMachineLocation: ${response.body}');

    var res = json.decode(response.body);
    logger.d(res['location']);
    return res['location'];
  }

  Stream<StaticBike> fetchStaticBikeStream(String userId) {
    // Create a local stream controller
    ctrl = StreamController<StaticBike>();

    // Store user locally
    _userId = userId;
    var channel = '{ "channel" : "' + userId + '" }';
    Utils.socket.emit('mobileConnected', channel);

    // Return the local stream
    return ctrl.stream;
  }

  void unsubscribeStaticBikeStream(String userId) {
    // redisPubsub.then(
    //   (pubsub) {
    //     pubsub.unsubscribe(channel: userId);
    //     _postReplySubscription?.cancel();
    //   },
    // );

    ctrl.close();
  }

  bool getSocketStatus() {
    return socketStatus;
  }
}
