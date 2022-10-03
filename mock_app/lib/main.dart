import 'package:flutter/material.dart';
import 'package:mock_app/qr_page.dart';
import 'rower_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RCP Demo',
      theme: ThemeData(
        primarySwatch: Colors.orange,
      ),
      home: MyHomePage(title: 'RCP Demo'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({key, @required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

void _openQRPage() {
  Navigator.push<void>(
    context,
    MaterialPageRoute<void>(
      builder: (BuildContext context) => QRPage(),
    ),
  );
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text(
              'RCP Demo: Rower',
            ),
            ElevatedButton(onPressed: _openQRPage, child: const Text("Scan QR Code")),
          ],
        ),
      ),
    );
  }
}
