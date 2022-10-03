import 'package:meta/meta.dart';

import 'package:myapp/repositories/repositories.dart';
import 'package:myapp/models/models.dart';
import 'package:myapp/repositories/common.dart';

class StaticBikeRepository {
  final StaticBikeApiClient staticBikeApiClient;

  StaticBikeRepository({@required this.staticBikeApiClient})
      : assert(staticBikeApiClient != null);

  Stream<StaticBike> fetchRepositoryStream(String user) {
    return staticBikeApiClient.fetchStaticBikeStream(user);
  }

  Stream<PostReplyEnum> fetchReplyStream(String user) {
    return staticBikeApiClient.fetchPostReplyStream(user);
  }

  void unsubscribeRepositoryStream(String user) async {
    staticBikeApiClient.unsubscribeStaticBikeStream(user);
  }

  void unsubscribeReplyStream(String user) async {
    staticBikeApiClient.unsubscribePostReplyStream(user);
  }

  void initializeWithUser(StaticBike input) {
    staticBikeApiClient.initializeWithUser(input.machineId, input.userId);

    // Connect to socket.io
    staticBikeApiClient.connect2SocketIO(input.machineId);
  }

  void resetUser(StaticBike input) {
    staticBikeApiClient.setUser(input.machineId, '');
  }

  void disconnectSocketIO() {
    staticBikeApiClient.disconnectSocketIO();
  }

  Future<String> getMachineName(String machineId) async {
    return await staticBikeApiClient.getMachineName(machineId);
  }

  Future<String> getMachineLocation(String machineId) async {
    return await staticBikeApiClient.getMachineLocation(machineId);
  }

  Future<String> getRecordingFlag(String machineId) async {
    return await staticBikeApiClient.getRecordingFlag(machineId);
  }

  Future<String> getCadence(String machineId) async {
    return await staticBikeApiClient.getCadence(machineId);
  }

  Future<void> postExercise(StaticBike staticBike) async {
    //await staticBikeApiClient.postExerciseToMongo(staticBike);
    await staticBikeApiClient.postExerciseMongoApiCall(staticBike.machineId);
  }

  bool getSocketStatus() {
    return staticBikeApiClient.getSocketStatus();
  }
}
