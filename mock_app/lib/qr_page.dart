import 'package:flutter/material.dart';
import 'package:flutter/src/widgets/container.dart';
import 'package:flutter/src/widgets/framework.dart';
import 'package:mock_app/rower_page.dart';

class QRPage extends StatefulWidget {
  const QRPage({key});

  @override
  State<QRPage> createState() => _QRPageState();
}

class _QRPageState extends State<QRPage> {
  @override

void _openRowerPage() {
  Navigator.push<void>(
    context,
    MaterialPageRoute<void>(
      builder: (BuildContext context) => RowerPage(),
    ),
  );
}

  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(child:Text("QR Page")),
        ElevatedButton(onPressed: _openRowerPage, child: Text("Next"))
        ]
    );
  }
}