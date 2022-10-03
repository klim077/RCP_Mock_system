import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'custom_timer_bloc.dart';

// ignore: must_be_immutable
class WorkoutCounterCard extends StatefulWidget {
  // const WorkoutCounterCard({ Key? key }) : super(key: key);
  final String parameter;
  final Widget counter;
  final bool average;
  double totalWorkoutTime;
  CustomTimerBloc workoutTimer;
  bool isNsFit;

  WorkoutCounterCard(
      {@required this.parameter,
      @required this.counter,
      @required this.average,
      this.totalWorkoutTime = 0,
      this.workoutTimer,
      this.isNsFit = false});
  @override
  _WorkoutCounterCardState createState() => _WorkoutCounterCardState();
}

class _WorkoutCounterCardState extends State<WorkoutCounterCard> {
  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Row(
          children: [
            Expanded(
              flex: 2,
              child: Column(
                children: [
                  widget.isNsFit
                      ? Padding(
                          padding: const EdgeInsets.only(top: 20.0),
                          child: Text(
                            widget.parameter.toUpperCase(),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: widget.average
                                  ? Colors.grey[600]
                                  : Colors.blueGrey[900],
                              fontSize: widget.average ? 12 : 14,
                            ),
                          ),
                        )
                      : Text(
                          widget.parameter.toUpperCase(),
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: widget.average
                                ? Colors.grey[600]
                                : Colors.blueGrey[900],
                            fontSize: widget.average ? 12 : 14,
                          ),
                        ),
                  widget.isNsFit
                      ? Padding(
                          padding: const EdgeInsets.only(left: 0.0),
                          child: BlocBuilder(
                            bloc: widget.workoutTimer,
                            builder: (context, state) {
                              return Text(
                                (state.duration < (widget.totalWorkoutTime / 6))
                                    ? 'Warm Up\n Phase'
                                    : (state.duration <
                                            (widget.totalWorkoutTime / 6) * 5)
                                        ? 'Running\n Phase'
                                        : 'Cool Down\n Phase',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: state.duration <
                                          (widget.totalWorkoutTime / 6)
                                      ? Colors.orange
                                      : state.duration <
                                              (widget.totalWorkoutTime / 6) * 5
                                          ? Colors.red
                                          : Colors.green,
                                ),
                                textAlign: TextAlign.center,
                              );
                            },
                          ),
                        )
                      : Container(),
                ],
              ),
            ),
            Expanded(
              flex: 3,
              child: Align(
                  alignment: Alignment.centerRight, child: widget.counter),
            ),
          ],
        ),
      ],
    );
  }
}
