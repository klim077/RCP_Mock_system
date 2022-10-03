import 'dart:async';
// import 'dart:math';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';
import 'package:myapp/blocs/blocs.dart';
import 'package:bloc/bloc.dart';
import 'package:myapp/blocs/custom_timer_bloc.dart';
import 'package:myapp/models/loginModel.dart';
import 'package:myapp/models/models.dart';
import 'package:myapp/repositories/repositories.dart';
import 'package:myapp/repositories/common.dart';

//import 'package:myapp/blocs/timer_bloc.dart';
//import 'package:myapp/models/ticker.dart';

/* -------------------------------------------------------------------------- */
/*                                    Event                                   */
/* -------------------------------------------------------------------------- */

@immutable
abstract class StaticBikeEvent extends Equatable {
  @override
  List<Object> get props => [];
}

class EmptyBikeEvent extends StaticBikeEvent {}

class BikeInitializeEvent extends StaticBikeEvent {
  final String machineId;
  final String userId;
  final CustomTimerBloc timerBloc;

  // Event should take the input as arguments
  BikeInitializeEvent(
      {@required this.machineId,
      @required this.userId,
      @required this.timerBloc})
      : assert(machineId != null),
        assert(userId != null),
        super();
  @override
  List<Object> get props => [
        machineId,
        userId,
        timerBloc,
      ];
}

class BikeStartRecordingEvent extends StaticBikeEvent {}

class RequestDummyDataEvent extends StaticBikeEvent {}

class BikeUpdateEvent extends StaticBikeEvent {
  final StaticBike staticBike;

  BikeUpdateEvent({@required this.staticBike})
      : assert(staticBike != null),
        super();
  @override
  List<Object> get props => [staticBike];
}

class StartWorkoutEvent extends StaticBikeEvent {}

class BikeStopWorkoutEvent extends StaticBikeEvent {}

class BikeClearingPopUp extends StaticBikeEvent {}

class BikeStopWorkoutWithoutSaving extends StaticBikeEvent {}

class BikeStopWorkoutWithSaving extends StaticBikeEvent {}

// class CheckUserPedallingEvent extends StaticBikeEvent {}

class BikePostExerciseEvent extends StaticBikeEvent {}

class BikeTick extends StaticBikeEvent {
  final int duration;

  BikeTick({@required this.duration}) : super();

  @override
  String toString() => "BikeTick { duration: $duration }";
  @override
  List<Object> get props => [duration];
}

/* -------------------------------------------------------------------------- */
/*                                    State                                   */
/* -------------------------------------------------------------------------- */

@immutable
abstract class StaticBikeState extends Equatable {
  @override
  List<Object> get props => [];
}

class InitialStaticBikeState extends StaticBikeState {
  @override
  String toString() => 'InitialStaticBikeState';
}

class StaticBikeEmptyState extends StaticBikeState {
  @override
  String toString() => 'StaticBikeEmptyState';
}

class StaticBikeNotReceivingDataState extends StaticBikeState {
  @override
  String toString() => 'StaticBikeNotReceivingData';
}

class StaticBikeReadyState extends StaticBikeState {
  final StaticBike staticBike;
  final String userDisplayName;
  final duration = 0;

  StaticBikeReadyState({@required this.staticBike, this.userDisplayName})
      : assert(staticBike != null),
        assert(userDisplayName != null),
        super();

  @override
  String toString() => 'StaticBikeReadyState';
  @override
  List<Object> get props => [staticBike, userDisplayName, duration];
}

class StaticBikeListeningState extends StaticBikeState {
  final StaticBike staticBike;
  final int duration;
  final String userDisplayName;

  StaticBikeListeningState({
    @required this.staticBike,
    @required this.duration,
    @required this.userDisplayName,
  })  : assert(staticBike != null),
        assert(duration != null),
        assert(userDisplayName != null),
        super();

  @override
  String toString() => 'StaticBikeListeningState';
  @override
  List<Object> get props => [staticBike, duration, userDisplayName];
}

class StaticBikeWorkingOutState extends StaticBikeState {
  final StaticBike staticBike;
  final String userDisplayName;

  StaticBikeWorkingOutState({
    @required this.staticBike,
    @required this.userDisplayName,
  })  : assert(staticBike != null),
        assert(userDisplayName != null),
        super();

  @override
  String toString() => 'StaticBikeWorkingOutState';
  @override
  List<Object> get props => [staticBike, userDisplayName];
}

class StaticBikeDoneState extends StaticBikeState {
  final StaticBike staticBike;
  final String userDisplayName;

  StaticBikeDoneState({
    @required this.staticBike,
    @required this.userDisplayName,
  })  : assert(staticBike != null),
        assert(userDisplayName != null),
        super();

  String toString() => 'StaticBikeDoneState';
  @override
  List<Object> get props => [staticBike, userDisplayName];
}

class StaticBikeClearPopUpState extends StaticBikeState {
  String toString() => 'Clearing pop up state in static bike';
}

class StaticBikeErrorState extends StaticBikeState {
  String toString() => 'StaticBikeError';
}

/* -------------------------------------------------------------------------- */
/*                                    Bloc                                    */
/* -------------------------------------------------------------------------- */

class StaticBikeBloc extends Bloc<StaticBikeEvent, StaticBikeState> {
  final StaticBikeRepository staticBikeRepository;
  StreamSubscription<StaticBike> _staticBikeSubscription;
  StreamSubscription<int> _tickerSubscription;

  bool socketStatus = false;

  StaticBike _staticBike;
  final WorkoutBloc workoutBloc;
  final TabletBloc tabletBloc;

  // String _phoneNo;
  String _userDisplayName;

  CustomTimerBloc workoutTimer;

  MyTicker _ticker;
  int currentWorkoutDuration = 0;

  bool userPedalBool = false;

  String _machineId = "";

  bool stopWorkoutFlag = false;

  StreamSubscription<PostReplyEnum> _postReplySubscription;

  _setCurrentStaticBike(BikeUpdateEvent event) {
    _staticBike = event.staticBike;
  }

  Stream<StaticBikeState> _startTimer(BikeStartRecordingEvent event) async* {
    print("_startTimer function");

    _ticker = MyTicker();

    // yield StaticBikeWorkingOutState(staticBike: _staticBike);

    _tickerSubscription?.cancel();

    _tickerSubscription = _ticker.tick(ticks: 0).listen(
      (duration) {
        add(BikeTick(duration: duration));
      },
    );
  }

  Stream<StaticBikeState> _startListening(
      BikeStartRecordingEvent event) async* {
    // StaticBike is now in listening state
    // Yield with a new StaticBike model object
    print("_startListening");
    yield StaticBikeListeningState(
      staticBike: _staticBike,
      duration: currentWorkoutDuration,
      userDisplayName: _userDisplayName,
    );

    _staticBikeSubscription?.cancel();

    // Fetch the StaticBike model object stream subcription
    Stream<StaticBike> staticBikeStream =
        staticBikeRepository.fetchRepositoryStream(_staticBike.userId);

    // Start listening to the stream with a callback
    print("entering callback");

    _staticBikeSubscription = staticBikeStream.listen(
      // Callback defined here
      (staticBike) {
        print("Stream callback");
        print(staticBike);

        // Keep a local copy
        _staticBike = staticBike;

        // add a state internally
        add(BikeUpdateEvent(staticBike: _staticBike));

        print("@BikeDataCallBAck, currentState: $state");
      },
    );
    print("exit callback");
  }

  void setUserPedalBool() async {
    String pedalFlag =
        (await staticBikeRepository.getRecordingFlag(_machineId));

    if (pedalFlag == "True")
      userPedalBool = true;
    else
      userPedalBool = false;

    // userPedalBool = true; //for testing
  }

  StaticBikeBloc({
    @required this.staticBikeRepository,
    @required this.workoutBloc,
    @required this.tabletBloc,
  })  : assert(staticBikeRepository != null),
        assert(workoutBloc != null);

  @override
  StaticBikeState get initialState => StaticBikeEmptyState();

  void setTimerBloc(CustomTimerBloc workoutTimer) =>
      workoutTimer = workoutTimer;

  @override
  Stream<StaticBikeState> mapEventToState(
    StaticBikeEvent event,
  ) async* {
    if (event is EmptyBikeEvent) {
      print("Event, StaticBikeEmpty");
      // yield* _startCalibrateTimer(event);
      yield StaticBikeEmptyState(); //staticBike: _staticBike);
    }

    if (event is BikeInitializeEvent) {
      print('static_bike_bloc: initialize.\n'
          'MachineID: ${event.machineId},\n'
          'UserID: ${event.userId}');

      // Get machine name
      String machineName =
          await staticBikeRepository.getMachineName(event.machineId);

      // Get machine location
      String machineLocation =
          await staticBikeRepository.getMachineLocation(event.machineId);

      userPedalBool = false;
      _machineId = event.machineId;
      // Create a new StaticBike object
      _staticBike = StaticBike(
        machineId: event.machineId,
        machineLocation: machineLocation,
        machineName: machineName,
        exerciseGroup: 'cardio',
        userId: event.userId,
      );

      // Assign user to machine
      // Reset machine values
      staticBikeRepository.initializeWithUser(_staticBike);
      setUserPedalBool();
      stopWorkoutFlag = false;

      User user = await tabletBloc.userRepository.getUserInfo(event.userId);
      // _phoneNo = Utils().maskPhoneNumber(user.phoneNo);
      _userDisplayName = user.name;

      yield StaticBikeReadyState(
          staticBike: _staticBike, userDisplayName: _userDisplayName);
    }

    if (event is BikeStartRecordingEvent) {
      print("bloc, event BikeStartRecording");

      yield* _startListening(event);
      yield* _startTimer(event);
    }

    if (event is StartWorkoutEvent) {
      print("MapEvent to State: StartWorkOutEvent");
      workoutTimer.add(CustomStart());
      print("start workout");
      //yield* _startTimer(event);

      yield StaticBikeWorkingOutState(
        staticBike: _staticBike,
        userDisplayName: _userDisplayName,
      );
    }

    if (event is BikeUpdateEvent) {
      //yield* _update(event);
      _setCurrentStaticBike(event);
      //updateUserPedallingBoolean(event);
    }

    if (event is BikeTick) {
      if (_staticBike.speed != 0.0 && workoutTimer != null) {
        print('speed: ${_staticBike.speed}');
        currentWorkoutDuration = workoutTimer.getDuration();
      }
      if (event.duration - currentWorkoutDuration > 60) {
        yield StaticBikeNotReceivingDataState();
        print('time out over');
        return;
      }

      //checkWorkoutState();
      // StaticBikeState state = currentState;
      print("Tick Event, $currentWorkoutDuration");

      setUserPedalBool();
//need set back to userPedalBool
      if (true) {
        print("User is pedalling");

        if (state is StaticBikeListeningState) {
          print("add StartWorkOutEvent");
          add(StartWorkoutEvent());
        } else if (state is StaticBikeWorkingOutState) {
          yield StaticBikeWorkingOutState(
            staticBike: _staticBike,
            userDisplayName: _userDisplayName,
          );
        }
      }
    }

    if (event is BikeUpdateEvent) {
      _staticBike = event.staticBike;
    }
    if (event is BikeStopWorkoutEvent) {
      if (currentWorkoutDuration > 30) {
        add(BikeStopWorkoutWithSaving());
      } else {
        add(BikeStopWorkoutWithoutSaving());
      }
    }

    if (event is BikeStopWorkoutWithSaving) {
      print("Bike Stop Workout event, saving...");
      // add an event to save exercise to database
      add(BikePostExerciseEvent());
      yield StaticBikeDoneState(
          staticBike: _staticBike, userDisplayName: _userDisplayName);

      workoutTimer.add(CustomReset());
      _staticBikeSubscription?.cancel();
      staticBikeRepository.disconnectSocketIO();

      staticBikeRepository.unsubscribeRepositoryStream(_staticBike.userId);
      _tickerSubscription?.cancel();
      tabletBloc.add(WorkoutSavedEvent());
    }

    if (event is BikeClearingPopUp) {
      yield StaticBikeClearPopUpState();
    }

    if (event is BikeStopWorkoutWithoutSaving) {
      print("Bike Stop Workout event, not saving...");
      // Cancel the subscriptions

      workoutTimer.add(CustomReset());
      _staticBikeSubscription?.cancel();

      staticBikeRepository.unsubscribeRepositoryStream(_staticBike.userId);
      _tickerSubscription?.cancel();
      staticBikeRepository.disconnectSocketIO();
      // add an event to save exercise to database
      yield StaticBikeDoneState(
          staticBike: _staticBike, userDisplayName: _userDisplayName);

      tabletBloc.add(WorkoutEndedEvent());
    }

    if (event is BikePostExerciseEvent) {
      // Check if there is anything to post
      //if (_staticBike.cadence > 0) {
      print("BikePostExerciseEvent");

      if (_staticBike != null) {
        // Fetch the postReply stream
        Stream<PostReplyEnum> postReplyStream =
            staticBikeRepository.fetchReplyStream(_staticBike.userId);

        // Subscribe to the postReply
        _postReplySubscription = postReplyStream.listen(
          // Define callback here
          (reply) {
            switch (reply) {
              case PostReplyEnum.Posted:
                // Let parent bloc know
                workoutBloc.add(
                  NotifyUpdateCompleted(userId: _staticBike.userId),
                );

                // Cancel the subscription
                _postReplySubscription?.cancel();
                //_tickerSubscription?.cancel();

                staticBikeRepository.unsubscribeReplyStream(_staticBike.userId);
                staticBikeRepository.disconnectSocketIO();

                tabletBloc.add(WorkoutSavedEvent());

                break;
            }
          },
        );

        // Use repository to post the exercise to database
        staticBikeRepository.postExercise(_staticBike);
      }
      workoutBloc.add(EndWorkout(isSuccess: true));
    }
  }

  String getMachineLocation() {
    return _staticBike.machineLocation;
  }
}
// _setTimerDuration(Tick event) => currentWorkoutDuration = event.duration;
