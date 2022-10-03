import 'package:flutter/material.dart';
import 'custom_timer_bloc.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'text.dart';

class CountUpTimer extends StatelessWidget {
  final CustomTimerBloc customTimerBloc;
  CountUpTimer({@required this.customTimerBloc});

  static const TextStyle timerTextStyle = TextStyle(
    fontSize: 25,
    fontWeight: FontWeight.normal,
  );

  @override
  Widget build(BuildContext context) {
    print("TimerWidget Build FunCtion");

    return Container(
      padding: EdgeInsets.fromLTRB(0, 10, 0, 0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          // Text(
          //   "WORKOUT TIME",
          //   style: TextStyle(fontSize: 14),
          //   textAlign: TextAlign.center,
          // ),
          Center(
            child: BlocBuilder(
              bloc: customTimerBloc,
              builder: (context, state) {
                final String hoursStr =
                    ((state.duration / 60) / 60).floor().toString();

                final String minutesStr = ((state.duration / 60) % 60)
                    .floor()
                    .toString()
                    .padLeft(2, '0');
                final String secondsStr =
                    (state.duration % 60).floor().toString().padLeft(2, '0');
                return Text(
                  '$hoursStr:$minutesStr:$secondsStr',
                  style: timerTextStyle,
                );
              },
            ),
          ),
          Text(
            ConstantText.timeUnit,
            style: TextStyle(
              color: Theme.of(context).textTheme.caption.color,
              fontSize: 12,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
