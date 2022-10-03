import 'package:flutter/material.dart';
import 'custom_timer_bloc.dart';

import 'package:flutter_bloc/flutter_bloc.dart';
// import 'package:myapp/widgets/bottom_info_row.dart';
import 'text.dart';
//import 'dart:math' as math;

//Timer
import 'count_up_timer_widget.dart';

import 'button_widget.dart';
import 'workout_counter_card.dart';

class RowerWidget extends StatefulWidget {
  final String machineId;
  final String userId;

  RowerWidget({
    Key key,
    @required this.machineId,
    @required this.userId,
  }) : super(key: key);

  @override
  _RowerWidget createState() => _RowerWidget();
}

class _RowerWidget extends State<RowerWidget> {
  String _machineId;
  String _userId;
  String socketStatusValue = "";

  String _machineLocation = '';
  String _machineName = '';
  var _titleInformation = {"machineName": '', "machineLocation": ''};

  RowerBloc _rowerBloc;

  double largeDetailCard = 1.2;
  double smallDetailCard = 0.8;

  bool confirmStopDialogVisible = false;

  // WearableBloc _wearableBloc;
  // bool _displayWearable = true;
  // bool _displayNsFit = false;

  //Rower dummyRower;
  Rower dummyRower = Rower(
      machineLocation: ' ',
      machineName: ' ',
      machineId: ' ',
      userId: ' ',
      exerciseGroup: 'cardio',
      speed: double.nan,
      cadence: double.nan,
      distance: double.nan,
      calories: double.nan,
      power: double.nan,
      currentAvgCadence: double.nan,
      currentAvgSpeed: double.nan);

  // @override
  // void dispose() {
  //   _wearableBloc.add(StopConnection());
  //   super.dispose();
  // }

  @override
  void didChangeDependencies() {
    print("@didChangeDependencies Method");
    if (mounted) {
      _machineId = widget.machineId;
      _userId = widget.userId;
      _rowerBloc = BlocProvider.of<RowerBloc>(context);
      // _wearableBloc = BlocProvider.of<WearableBloc>(context);

      _setMachineInfo();

      final state = _rowerBloc.state;
      print("State is");
      print(state);

      if (state is RowerEmptyState) {
        print("didChangeDependencies state is RowerEmptyState ");

        print("Machine ID is $_machineId");

        _rowerBloc.add(RowerInitializeEvent(
          userId: _userId,
          machineId: _machineId,
          timerBloc: _rowerBloc.workoutTimer,
        ));

        _rowerBloc.setTimerBloc(_rowerBloc.workoutTimer);
      }

      if (state is RowerListeningState) {
        print("@didChangeDependencies: state is RowerListeningState ");
        _machineId = state.rower.machineId;
        _userId = state.rower.userId;
        print(_machineId);
        print(_userId);
        print("Machine Info");
        print(_titleInformation);
      }

      if (state is RowerDoneState) {
        _machineId = state.rower.machineId;
        _userId = state.rower.userId;
      }

      if (state is RowerWorkingOutState) {
        _machineId = state.rower.machineId;
        _userId = state.rower.userId;
        print(_machineId);
      }
    }
    super.didChangeDependencies();
  }

  void closeDialog() {
    Navigator.pop(context);
  }

  Widget liveData(Rower rower, String userDisplayName) {
    // socketStatus(phoneNo);

    // if (MediaQuery.of(context).orientation == Orientation.portrait) {
    //   return portraitView(rower, phoneNo);
    // } else {
    return landscapeView2(rower, userDisplayName);
    // }
  }

  Widget loadingConfig(Rower rower) {
    // socketStatus(phoneNo);

    // to support portrait view in future
    return loadingCalibrateWidget(rower);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: blocSetup(),
    );
  }

  Future<void> _setMachineInfo() async {
    // Get machine name
    _machineName =
        await _rowerBloc.rowerRepository.getMachineName(_machineId);

    print("machineName from redis $_machineName");

    if (_machineName == null) _machineName = "Rower";

    print("machineName from redis $_machineName");

    // Get machine location
    _machineLocation = await _rowerBloc.rowerRepository
        .getMachineLocation(_machineId);

    _titleInformation = {
      "machineName": _machineName,
      "machineLocation": _machineLocation
    };

    print("Finish Set Machine Info");
    print(_titleInformation);
  }

  Widget blocSetup() {
    return Center(
      child: Container(
          child: BlocListener<RowerBloc, RowerState>(
        bloc: _rowerBloc,
        listener: (BuildContext context, RowerState state) {
          if (state is RowerNotReceivingDataState) {
            showDialog(
              context: context,
              barrierDismissible: false,
              builder: (BuildContext context) {
                return _rowerNotStartingPopUp();
              },
            );
          }
          if (state is RowerListeningState) {
            // showDialog(
            //   context: context,
            //   barrierDismissible: false,
            //   builder: (BuildContext context) {
            //     return _rowerNotStartingPopUp();
            //   },
            // );
          }
          if (state is RowerClearPopUpState) {
            if (confirmStopDialogVisible) {
              closeDialog();
            }
            Future.delayed(const Duration(milliseconds: 1000), () {
              _rowerBloc.add(RowerStopWorkoutEvent());
            });
          }
        },
        child: BlocBuilder(
          bloc: _rowerBloc,
          builder: (BuildContext context, RowerState state) {
            print("_buildRowerDataBloc State: $state");

            if (state is RowerReadyState) {
              print("UI Bloc - RowerReady");

              // _displayWearable =
              //     _rowerBloc.getMachineLocation().contains('10MBCLevel9');

              _rowerBloc.add(RowerStartRecordingEvent());

              return loadingConfig(dummyRower);
              // return liveData(state.rower, state.phoneNo);
              //return CircularProgressIndicator(); //Show a message "StartWorkOut"
            }

            if (state is RowerEmptyState) {
              // return liveData(dummyRower, socketStatusValue);
              return loadingConfig(dummyRower);
            }

            if (state is RowerListeningState) {
              print(
                  "daBloc RowerListeningState, timerBloc ${_rowerBloc.workoutTimer.state.toString()}");

              if (state.rower.speed != null) {
                print(state.rower.toString());
                return liveData(state.rower, state.userDisplayName);
              } else {
                print("_RowerBloc, Rower.speed == null");
                return loadingConfig(dummyRower);
              }
            }

            if (state is RowerWorkingOutState) {
              //Navigator.pop(context); //To dismiss PauseWorkout Dialog
              print("_buildRowerDataBloc, RowerWorkingOut");
              print("Speed ${state.rower}");
              if (state.rower.speed != null) {
                return liveData(state.rower, state.userDisplayName);
              } else {
                return liveData(dummyRower, state.userDisplayName);
              }
            }

            if (state is RowerDoneState) {
              print("daBloc RowerDone");
              _rowerBloc.workoutTimer.add(CustomReset());
              return liveData(state.rower, state.userDisplayName);
            }

            return Container();
          },
        ),
      )),
    );
  }

  Widget landscapeView2(Rower rower, String userDisplayName) {
    return Row(
      children: [
        Expanded(flex: 1, child: Container()),
        Expanded(
          flex: 24,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Expanded(
                flex: 1,
                child: Container(),
              ),
              Expanded(
                flex: 2,
                child: _machineHeader(),
              ),
              Expanded(
                flex: 18,
                child: Row(
                  children: [
                    Expanded(
                      flex: 5,
                      child: _rowerWorkoutData(rower),
                    ),
                    Expanded(
                      flex: 2,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // _displayNsFit
                          //     ? NsfitTask(
                          //         result: [false, false],
                          //       )
                          //     : Container(),
                          // _displayNsFit
                          //     ? NsfitProgress(
                          //         activeExerciseGroup: rower.exerciseGroup,
                          //       )
                          //     : Container(),
                          // _displayWearable
                          //     ? Align(
                          //         alignment: Alignment.topCenter,
                          //         child: Padding(
                          //           padding:
                          //               const EdgeInsets.only(left: 40, top: 0),
                          //           child: WearableWidget(
                          //             useButtonWidget: true,
                          //             periodicSync: true,
                          //           ),
                          //         ))
                              // : Container(),
                          Align(
                            alignment: Alignment.centerRight,
                            child: Padding(
                              padding: const EdgeInsets.only(bottom: 20),
                              child: Image.asset(
                                'assets/weighing-scale/sgymLogo.png',
                                scale: 30,
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  ],
                ),
              ),
              Expanded(
                flex: 3,
                child: SmartGymButtons().stopRecordingButton(_onPressedStop),
              ),
              Expanded(
                flex: 1,
                // child: BottomInfoRow(
                //   userDisplayName: userDisplayName,
                //   isKiosk: false,
                // ),
                child: Container(),
              ),
              Expanded(
                flex: 1,
                child: Container(),
              ),
            ],
          ),
        ),
        Expanded(flex: 1, child: Container()),
      ],
    );
  }

  // need support for portrait mode
  Widget loadingCalibrateWidget(Rower rower) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: <Widget>[
        Flexible(
          flex: 3,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: <Widget>[
              Flexible(flex: 1, child: Container()),
              Flexible(
                flex: 2,
                child: Text(
                  "Start Pedaling",
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headline4,
                ),
              ),
              Flexible(
                flex: 9,
                child: Image.asset(
                  'assets/rower.jpeg',
                  height: 400,
                  width: 400,
                ),
              ),
              Flexible(
                flex: 2,
                child: Text(
                  "Calibrating...",
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headline4,
                ),
              ),
              Flexible(flex: 1, child: Container()),
            ],
          ),
        )
      ],
    );
  }

  Widget _machineHeader() {
    return Text(
      _titleInformation['machineName'].toUpperCase(),
      textAlign: TextAlign.center,
      style: TextStyle(
        fontWeight: FontWeight.bold,
        color: Colors.blueGrey[900],
        fontSize: 25,
      ),
    );
  }

  Widget _RowerWorkoutData(Rower rower) {
    return Row(
      children: [
        Expanded(
          flex: 1,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(0, 20, 30, 20),
            child: Column(
              children: [
                Expanded(
                  flex: 1,
                  child: WorkoutCounterCard(
                    parameter: 'Time',
                    counter: workoutTime(),
                    average: false,
                  ),
                ),
                Divider(
                  color: Colors.blueGrey[400],
                ),
                Expanded(
                  flex: 1,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Padding(
                        padding: EdgeInsets.only(top: 35),
                        child: WorkoutCounterCard(
                            parameter: 'Speed',
                            counter: _rowerCounter(
                              value: rower.speed,
                              units: ConstantText.speedUnit,
                              precision: 1,
                            ),
                            average: false),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 10.0),
                        child: WorkoutCounterCard(
                            parameter: 'Average',
                            counter: _rowerAverageCounter(
                              value: rower.currentAvgSpeed,
                              units: ConstantText.speedUnit,
                              precision: 1,
                            ),
                            average: true),
                      ),
                    ],
                  ),
                ),
                Divider(
                  color: Colors.blueGrey[400],
                ),
                Expanded(
                  flex: 1,
                  child: WorkoutCounterCard(
                    parameter: 'Calories',
                    counter: _rowerCounter(
                      value: rower.calories,
                      units: ConstantText.caloriesUnit,
                      precision: 1,
                    ),
                    average: false,
                  ),
                ),
              ],
            ),
          ),
        ),
        Expanded(
          flex: 1,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 20),
            child: Column(
              children: [
                Expanded(
                  flex: 1,
                  child: WorkoutCounterCard(
                    parameter: 'Distance',
                    counter: _rowerCounter(
                      value: rower.distance,
                      units: ConstantText.distanceSIUnt,
                      precision: 2,
                    ),
                    average: false,
                  ),
                ),
                Divider(
                  color: Colors.blueGrey[400],
                ),
                Expanded(
                  flex: 1,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Padding(
                        padding: EdgeInsets.only(top: 35),
                        child: WorkoutCounterCard(
                            parameter: 'Cadence',
                            counter: _rowerCounter(
                              value: rower.cadence,
                              units: ConstantText.cadenceUnit,
                              precision: 1,
                            ),
                            average: false),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 10.0),
                        child: WorkoutCounterCard(
                            parameter: 'Average',
                            counter: _rowerAverageCounter(
                              value: rower.currentAvgCadence,
                              units: ConstantText.cadenceUnit,
                              precision: 1,
                            ),
                            average: true),
                      ),
                    ],
                  ),
                ),
                Divider(
                  color: Colors.blueGrey[400],
                ),
                Expanded(
                  flex: 1,
                  child: WorkoutCounterCard(
                    parameter: 'Power',
                    counter: _rowerCounter(
                      value: rower.speed,
                      units: ConstantText.powerUnit,
                      precision: 1,
                    ),
                    average: false,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _rowerCounter({
    double value,
    String units,
    int precision,
  }) {
    return Text(
      value != null
          ? value.isNaN
              ? '0 ' + units
              : value.toStringAsFixed(precision) + ' ' + units
          : '0 ' + units,
      textAlign: TextAlign.center,
      style: TextStyle(
        fontSize: 25.0,
        fontWeight: FontWeight.normal,
        color: Colors.blueGrey[900],
      ),
    );
  }

  Widget _rowerAverageCounter({
    double value,
    String units,
    int precision,
  }) {
    return Text(
      value != null
          ? value.isNaN
              ? '0 ' + units
              : value.toStringAsFixed(precision) + ' ' + units
          : '0 ' + units,
      textAlign: TextAlign.center,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.normal,
        color: Colors.grey[600],
      ),
    );
  }

  Widget workoutTime() {
    return Container(
      child: CountUpTimer(
        customTimerBloc: _rowerBloc.workoutTimer,
      ),
    );
  }

  AlertDialog _buildConfirmStopRecordingUnder30() {
    confirmStopDialogVisible = true;
    return AlertDialog(
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(
            'Do you want to stop recording?\nAny workout below 30 seconds will not be saved\n',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 17,
            ),
          ),
        ],
      ),
      actions: <Widget>[
        Padding(
          padding: const EdgeInsets.only(bottom: 15.0),
          child: Center(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SmartGymButtons().smallButton(_onPressedNo, 'No', false),
                SmartGymButtons().smallButton(_onPressedYes, 'Yes', true)
              ],
            ),
          ),
        ),
      ],
    );
  }

  AlertDialog _buildConfirmStopRecording() {
    confirmStopDialogVisible = true;
    return AlertDialog(
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(
            'Do you want to stop recording?\nThe workout will be saved when you exit\n',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 17,
            ),
          ),
        ],
      ),
      actions: <Widget>[
        Padding(
          padding: const EdgeInsets.only(bottom: 15.0),
          child: Center(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SmartGymButtons().smallButton(_onPressedNo, 'No', false),
                SmartGymButtons().smallButton(_onPressedYes, 'Yes', true)
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _onPressedNo() {
    confirmStopDialogVisible = false;
    Navigator.pop(context);
  }

  void _onPressedYes() {
    confirmStopDialogVisible = false;
    _rowerBloc.add(RowerStopWorkoutEvent());
    Navigator.pop(context);
  }

  void _onPressedStop() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        if (_rowerBloc.workoutTimer.getDuration() < 30) {
          return _buildConfirmStopRecordingUnder30();
        } else {
          return _buildConfirmStopRecording();
        }
      },
    );
  }

  AlertDialog _rowerNotStartingPopUp() {
    return AlertDialog(
      title: Center(
        child: Text(
          'Timeout',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(
            'We cannot detect any movement from the rower\n'
            'Please scan your QR again and restart the workout with the rower\n',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 17,
            ),
          ),
        ],
      ),
      actions: <Widget>[
        Center(
          child: SmartGymButtons().smallButton(_onPressedYes, 'OK', true),
        ),
      ],
    );
  }
}
