import 'dart:async';
import 'dart:ui';
// import 'dart:io';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';
import 'package:bloc/bloc.dart';
import 'ticker.dart';
///////////
// Events
//////////

@immutable
abstract class CustomTimerEvent extends Equatable {
  @override
  List<Object> get props => [];
}

class CustomStart extends CustomTimerEvent {
  CustomStart() : super();

  @override
  List<Object> get props => [];
}

class CustomRestart extends CustomTimerEvent {
  CustomRestart() : super();
  @override
  List<Object> get props => [];
}

class CustomPause extends CustomTimerEvent {
  @override
  String toString() => "Pause";
}

class CustomResume extends CustomTimerEvent {
  @override
  String toString() => "Resume";
}

class CustomReset extends CustomTimerEvent {
  @override
  String toString() => "Reset";
}

class CustomFinish extends CustomTimerEvent {
  @override
  String toString() => "Finish";
}

class CustomTimerTick extends CustomTimerEvent {
  final int duration;

  CustomTimerTick({@required this.duration}) : super();

  @override
  String toString() => "Tick { duration: $duration }";
  @override
  List<Object> get props => [duration];
}

class CustomTriggerFunnction extends CustomTimerEvent {
  final Function triggerFunction;

  CustomTriggerFunnction({@required this.triggerFunction});

  @override
  String toString() => "Reset";
  @override
  List<Object> get props => [triggerFunction];
}

///////////
// States
//////////

@immutable
abstract class CustomTimerState extends Equatable {
  final int duration;
  @override
  CustomTimerState(this.duration);
  List<Object> get props => [this.duration];
}

class CustomReady extends CustomTimerState {
  CustomReady() : super(0);

  @override
  String toString() => 'Ready { duration: $duration }';
}

class CustomPaused extends CustomTimerState {
  CustomPaused(int duration) : super(duration);

  @override
  String toString() => 'Paused { duration: $duration }';
}

class CustomRunning extends CustomTimerState {
  CustomRunning(int duration) : super(duration);

  @override
  String toString() => 'Running { duration: $duration }';
}

class CustomFinished extends CustomTimerState {
  CustomFinished() : super(0);

  @override
  String toString() => 'Finished';
}

///////////
// Bloc
//////////

class CustomTimerBloc extends Bloc<CustomTimerEvent, CustomTimerState> {
  int _duration = 0;
  final int startDuration;
  final _ticker;
  VoidCallback triggerFunction;
  final int timerEndDuration;

  StreamSubscription<int> _tickerSubscription;

  CustomTimerBloc(
      {@required ticker,
      @required this.timerEndDuration,
      @required this.startDuration,
      VoidCallback triggerFunction})
      : assert(ticker != null),
        _ticker = ticker,
        triggerFunction = triggerFunction ?? (() {}),
        super(CustomReady()) {
    _duration = startDuration;

    on<CustomStart>(_onEventStart);
    on<CustomFinish>(_onEventFinish);
    on<CustomRestart>(_onEventRestart);
    on<CustomResume>(_onEventResume);
    on<CustomReset>(_onEventReset);
    on<CustomTimerTick>(_onEventTick);
    on<CustomPause>(_onEventPause);
    on<CustomTriggerFunnction>((event, emit) async {
      this.triggerFunction = event.triggerFunction;
    });
  }

  void addTriggerFunction({@required VoidCallback triggerFunction}) {
    this.triggerFunction = triggerFunction;
  }

  // @override
  // CustomTimerState get initialState => CustomReady(_duration);

  // @override
  // Stream<CustomTimerState> mapEventToState(
  //   CustomTimerEvent event,
  // ) async* {
  //   if (event is CustomStart) {
  //     yield* _mapStartToState(event);
  //   } else if (event is CustomTimerTick) {
  //     yield* _mapTickToState(event);
  //   } else if (event is CustomFinish) {
  //     yield* _mapFinishedToState(event);
  //   } else if (event is CustomRestart) {
  //     yield* _mapRestartToState(event);
  //   } else if (event is CustomResume) {
  //     yield* _mapResumeToState(event);
  //   } else if (event is CustomReset) {
  //     yield* _mapResetToState(event);
  //   } else if (event is CustomTimerTick) {
  //     yield* _mapTickToState(event);
  //   } else if (event is CustomPause) {
  //     yield* _mapPauseToState(event);
  //   } else if (event is CustomTriggerFunnction) {
  //     triggerFunction = event.triggerFunction;
  //   }
  // }

  int getDuration() => _duration;
  void setDuration(int dur) {
    _duration = dur;
  }

  void _onEventStart(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    print("Map Start to State");
    if (startDuration == _duration) {
      emit(CustomRunning(_duration));
      _tickerSubscription?.cancel();
      _tickerSubscription = _ticker.tick(ticks: _duration).listen(
        (duration) {
          add(CustomTimerTick(duration: duration));
        },
      );
    }
  }

  void _onEventFinish(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    print("Map Start to State");
    _tickerSubscription?.cancel();
    emit(CustomFinished());
    // yield CustomReady(0);
  }

  void _onEventRestart(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    print("Map Start to State");

    emit(CustomRunning(startDuration));
    _tickerSubscription?.cancel();
    _tickerSubscription = _ticker.tick(ticks: startDuration).listen(
      (duration) {
        add(CustomTimerTick(duration: duration));
      },
    );
  }

  void _onEventPause(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    // final state = currentState;
    if (state is CustomRunning) {
      _tickerSubscription?.pause();
      emit(CustomPaused(state.duration));
    }
  }

  void _onEventTick(CustomTimerTick tick, Emitter<CustomTimerState> emit) {
    //yield tick.duration > 0 ? Running(tick.duration) : Finished();
    emit(CustomRunning(tick.duration));
    _duration = tick.duration;
    if (timerEndDuration == -1) {
      return;
    }
    if (_ticker is MyTicker) {
      if (timerEndDuration <= tick.duration) {
        add(CustomFinish());
        this.triggerFunction();
      }
    } else {
      if (timerEndDuration >= tick.duration) {
        add(CustomFinish());
        this.triggerFunction();
      }
    }
  }

  void _onEventResume(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    // final state = currentState;
    if (state is CustomPaused) {
      _tickerSubscription?.resume();
      emit(CustomRunning(state.duration));
    }
  }

  void _onEventReset(CustomTimerEvent event, Emitter<CustomTimerState> emit) {
    _tickerSubscription?.cancel();
    _duration = startDuration;
    emit(CustomReady());
  }

  // Stream<CustomTimerState> _mapStartToState(CustomStart start) async* {
  //   print("Map Start to State");
  //   if (startDuration == _duration) {
  //     yield CustomRunning(_duration);
  //     _tickerSubscription?.cancel();
  //     _tickerSubscription = _ticker.tick(ticks: _duration).listen(
  //       (duration) {
  //         add(CustomTimerTick(duration: duration));
  //       },
  //     );
  //   }
  // }

  // Stream<CustomTimerState> _mapFinishedToState(CustomFinish start) async* {
  //   print("Map Start to State");
  //   _tickerSubscription?.cancel();
  //   yield CustomFinished();
  //   // yield CustomReady(0);
  // }

  // Stream<CustomTimerState> _mapRestartToState(CustomRestart restart) async* {
  //   print("Map Start to State");

  //   yield CustomRunning(startDuration);
  //   _tickerSubscription?.cancel();
  //   _tickerSubscription = _ticker.tick(ticks: startDuration).listen(
  //     (duration) {
  //       add(CustomTimerTick(duration: duration));
  //     },
  //   );
  // }

  // Stream<CustomTimerState> _mapPauseToState(CustomPause pause) async* {
  //   // final state = currentState;
  //   if (state is CustomRunning) {
  //     _tickerSubscription?.pause();
  //     yield CustomPaused(state.duration);
  //   }
  // }

  // Stream<CustomTimerState> _mapTickToState(CustomTimerTick tick) async* {
  //   //yield tick.duration > 0 ? Running(tick.duration) : Finished();
  //   yield CustomRunning(tick.duration);
  //   _duration = tick.duration;
  //   if (timerEndDuration == -1) {
  //     return;
  //   }
  //   if (_ticker is MyTicker) {
  //     if (timerEndDuration <= tick.duration) {
  //       add(CustomFinish());
  //       triggerFunction();
  //     }
  //   } else {
  //     if (timerEndDuration >= tick.duration) {
  //       add(CustomFinish());
  //       triggerFunction();
  //     }
  //   }
  // }

  // Stream<CustomTimerState> _mapResumeToState(CustomResume pause) async* {
  //   // final state = currentState;
  //   if (state is CustomPaused) {
  //     _tickerSubscription?.resume();
  //     yield CustomRunning(state.duration);
  //   }
  // }

  // Stream<CustomTimerState> _mapResetToState(CustomReset reset) async* {
  //   _tickerSubscription?.cancel();
  //   _duration = startDuration;
  //   yield CustomReady(startDuration);
  // }
}
