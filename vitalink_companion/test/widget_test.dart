// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:vitalink_companion/main.dart';

void main() {
  testWidgets('VitaLink app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const VitaLinkApp());

    // Verify that the splash screen is shown
    expect(find.text('VitaLink Companion'), findsOneWidget);
    expect(find.text('La tua app per la gestione pazienti'), findsOneWidget);
  });
}
