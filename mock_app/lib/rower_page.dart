import 'dart:html';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:mock_app/rower_widget.dart';

class RowerPage extends StatefulWidget {
  @override 
  _RowerPageState createState() => _RowerPageState();
}

class _RowerPageState extends State<RowerPage> {
  var _machineId = "cd44558bb2454746a9a7c6b8c1fd4716";

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        // decoration: BoxDecoration(
        //   image: DecorationImage(
        //     // colorFilter: new ColorFilter.mode(Colors.white.withOpacity(0.00), BlendMode.dstATop),
        //     image: AssetImage("rower.jpeg"),
        //     fit: BoxFit.cover,
        //     scale:100, ) 
        //   ),
          child: RowerWidget(
            machineId: "abc",
            userId: "123",
          ),)
      );
  }
}