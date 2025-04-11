import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
// Removed speech_to_text import as it's no longer used
// import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'dart:io';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:google_ml_kit/google_ml_kit.dart';
import 'package:flutter/foundation.dart'; // For debugPrint

// --- Imports for other pages ---
import 'settings_page.dart';
import 'suggestions_page.dart';
import 'insights_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FinvisionAI',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MediaSelectionPage(),
    );
  }
}

// Main container with Bottom Navigation Bar
class MediaSelectionPage extends StatefulWidget {
  const MediaSelectionPage({super.key});

  @override
  _MediaSelectionPageState createState() => _MediaSelectionPageState();
}

class _MediaSelectionPageState extends State<MediaSelectionPage> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const ExpenseScannerPage(),
    const InsightsPage(),
    const SuggestionsPage(),
    const SettingsPage(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _onItemTapped,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Transactions'),
          NavigationDestination(icon: Icon(Icons.timeline), label: 'Insights'),
          NavigationDestination(icon: Icon(Icons.lightbulb), label: 'Suggestion'),
          NavigationDestination(icon: Icon(Icons.more_horiz), label: 'More'),
        ],
      ),
    );
  }
}


// --- PulsatingMicButton Widget REMOVED ---


// --- ExpenseScannerPage Widget ---
class ExpenseScannerPage extends StatefulWidget {
  const ExpenseScannerPage({Key? key}) : super(key: key);

  @override
  _ExpenseScannerPageState createState() => _ExpenseScannerPageState();
}

class _ExpenseScannerPageState extends State<ExpenseScannerPage> {
  File? _selectedImage;
  String _recognizedText = "";
  final ImagePicker _picker = ImagePicker();
  // Removed speech_to_text related variables
  // final stt.SpeechToText _speech = stt.SpeechToText();
  // bool _isListening = false;
  // String _spokenText = "";
  bool _showFabOptions = false;
  // Removed _enteredText variable
  // String? _enteredText;
  bool _isExpense = true;
  bool _isProcessingOCR = false;
  bool _isProcessingBill = false;
  String? _parseBillError;

  List<Widget>? _parsedResultWidgets;


  @override
  void initState() {
    super.initState();
    // Removed speech initialization call
    // _initializeSpeech();
  }

  // Helper to reset inputs and API states
  void _clearInputsAndErrors() {
    setState(() {
      _selectedImage = null;
      _recognizedText = "";
      // Removed _spokenText and _enteredText clearing
      // _spokenText = "";
      // _enteredText = null;
      _parseBillError = null;
      _parsedResultWidgets = null;
      _isProcessingOCR = false;
      _isProcessingBill = false;
    });
  }

  // Removed _initializeSpeech function
  // void _initializeSpeech() async { /* ... */ }

  Future<void> _pickImage(ImageSource source) async {
    if (_isProcessingOCR || _isProcessingBill) return;
    _clearInputsAndErrors();
    final XFile? image = await _picker.pickImage(source: source);
    if (image != null && mounted) {
      setState(() { _selectedImage = File(image.path); _isProcessingOCR = true; });
      await _performOCR(image);
    }
  }

  Future<void> _performOCR(XFile image) async {
    if (!mounted) return;
    try {
      final inputImage = InputImage.fromFilePath(image.path);
      final textRecognizer = GoogleMlKit.vision.textRecognizer();
      final recognizedText = await textRecognizer.processImage(inputImage);
      textRecognizer.close();
      if (mounted) {
        setState(() { _recognizedText = recognizedText.text; _isProcessingOCR = false; _parseBillError = null; _parsedResultWidgets = null; });
      }
    } catch(e) {
      print("Error during OCR: $e");
      if (mounted) {
        setState(() { _recognizedText = "Error performing OCR."; _isProcessingOCR = false; });
      }
    }
  }

  // --- Voice Input Methods REMOVED ---
  // void _startVoiceInput() async { /* ... */ }
  // void _stopVoiceInput() { /* ... */ }
  // void _showVoicePopup() { /* ... */ }

  // --- Manual Text Entry Method REMOVED ---
  // void _enterTextManually() { /* ... */ }

  // --- Function to call the /parse-bill endpoint (using _recognizedText only) ---
  Future<void> _processBillText() async {
    // Only process if not busy and OCR produced valid text
    if (_isProcessingBill || _isProcessingOCR || _recognizedText.isEmpty || _recognizedText == "Error performing OCR.") {
      debugPrint("Skipping processBillText. Busy: $_isProcessingBill/$_isProcessingOCR, Text: '${_recognizedText.isNotEmpty}'");
      if(_recognizedText.isEmpty || _recognizedText == "Error performing OCR.") {
        if(mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No valid text from image to process.')));
      }
      return;
    }

    if (!mounted) return;
    setState(() { _isProcessingBill = true; _parseBillError = null; _parsedResultWidgets = null; });

    const String url = "http://192.168.1.7:8012/parse-bill"; // <-- CHANGE IP IF NEEDED
    final String textToSend = _recognizedText; // ONLY use text from OCR

    debugPrint("--- ExpenseScanner: Processing Bill - Posting to $url ---");

    try {
      final response = await http.post(
        Uri.parse(url),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"text": textToSend}),
      ).timeout(const Duration(seconds: 30));

      debugPrint("--- ExpenseScanner: Process Bill - Response Status: ${response.statusCode} ---");
      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> productsRaw = data['classified_products'] ?? [];
        final List<Map<String, dynamic>> products = productsRaw.map((item) => item is Map ? Map<String, dynamic>.from(item) : null).whereType<Map<String, dynamic>>().toList();
        final double? total = (data['final_amount'] as num?)?.toDouble();

        // Build result widgets
        List<Widget> resultWidgets = [];
        resultWidgets.add(const Text("Parsed Results:", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueAccent)));
        resultWidgets.add(const SizedBox(height: 10));
        if (products.isNotEmpty) { /* ... add product listTiles ... */ }
        else { resultWidgets.add(const Text("No products identified.", style: TextStyle(fontStyle: FontStyle.italic))); resultWidgets.add(const SizedBox(height: 15)); }
        resultWidgets.add(const Text("Final Amount:", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)));
        resultWidgets.add(const Divider(thickness: 1.5));
        resultWidgets.add(Text(total != null ? "₹${total.toStringAsFixed(2)}" : "Not Found", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)));

        setState(() { _parsedResultWidgets = resultWidgets; _isProcessingBill = false; _parseBillError = null; });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Bill processed successfully!'), backgroundColor: Colors.green,));

      } else { /* ... handle server error ... */ }
    } catch (e) { /* ... handle network/other errors ... */ }
    finally { if (mounted && _isProcessingBill) { setState(() { _isProcessingBill = false; }); } }
  } // End _processBillText


  // --- Build FAB Option (Modified to remove unused options) ---
  Widget _buildFabOption(IconData icon, VoidCallback onPressed, String label, Color backgroundColor) {
    // Return a Column or Row depending on your desired layout for the remaining buttons
    return Padding( // Keep padding for consistency if desired
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Container( padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(4)), child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 12))),
          const SizedBox(width: 12),
          FloatingActionButton( heroTag: label, mini: true, backgroundColor: backgroundColor, child: Icon(icon, color: Colors.white),
            onPressed: () { if (mounted) setState(() => _showFabOptions = false); onPressed(); },
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    // Removed _speech calls
    super.dispose();
  }

  // --- Build Method (UI adjusted for removed inputs) ---
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // Only check for OCR text or selected image now
    bool hasContent = _selectedImage != null || (_recognizedText.isNotEmpty && _recognizedText != "Error performing OCR.");
    bool showProcessButton = _selectedImage != null && _recognizedText.isNotEmpty && _recognizedText != "Error performing OCR." && !_isProcessingOCR;

    return Scaffold(
      backgroundColor: theme.colorScheme.background,
      appBar: AppBar(
        title: Row( /* ... AppBar Title Row remains the same ... */ ),
        centerTitle: true,
      ),
      body: Padding( // Add overall padding
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // --- Display Area (Image only or Placeholder) ---
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (_selectedImage != null) // Only show image stuff if image selected
                      Column(
                        children: [
                          Container(
                            constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.35),
                            margin: const EdgeInsets.only(bottom: 10),
                            child: ClipRRect(borderRadius: BorderRadius.circular(12.0), child: Image.file(_selectedImage!, fit: BoxFit.contain)),
                          ),
                          if(_isProcessingOCR) const Padding( padding: EdgeInsets.only(top: 0, bottom: 5), child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [CircularProgressIndicator(strokeWidth: 2), SizedBox(width: 10), Text("Processing Image...")])),
                          if(!_isProcessingOCR && _recognizedText.isNotEmpty && _recognizedText != "Error performing OCR.") const Padding( padding: EdgeInsets.only(top: 0, bottom: 5), child: Text("OCR Complete", style: TextStyle(color: Colors.green, fontStyle: FontStyle.italic))),
                          if(!_isProcessingOCR && _recognizedText == "Error performing OCR.") Padding( padding: const EdgeInsets.only(top: 0, bottom: 5), child: Text(_recognizedText, style: const TextStyle(color: Colors.red))),
                        ],
                      )
                    else // Placeholder when no content
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 40.0),
                        child: Text(
                          'Use the + button to scan a bill', // Updated placeholder
                          style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.onBackground.withOpacity(0.7)),
                          textAlign: TextAlign.center,
                        ),
                      ),

                    // Processing Indicator and Error Display for /parse-bill
                    if (_isProcessingBill) const Padding( padding: EdgeInsets.symmetric(vertical: 15.0), child: CircularProgressIndicator(), ),
                    if (_parseBillError != null && !_isProcessingBill) Padding( padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 10.0), child: Text(_parseBillError!, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center), ),

                    // Process Button (Only shows after successful OCR)
                    if (showProcessButton) Padding( padding: const EdgeInsets.symmetric(vertical: 10.0), child: ElevatedButton.icon( icon: const Icon(Icons.send_and_archive_outlined), label: const Text("Process Image Text"), style: ElevatedButton.styleFrom( backgroundColor: Colors.blueAccent, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20), textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)), onPressed: _isProcessingBill ? null : _processBillText, ), ),

                    // Display Parsed Results
                    if (!_isProcessingBill && _parseBillError == null && _parsedResultWidgets != null)
                      Container(
                        margin: const EdgeInsets.only(top: 20.0),
                        padding: const EdgeInsets.all(16.0),
                        decoration: BoxDecoration( color: Colors.grey[200], borderRadius: BorderRadius.circular(12.0), border: Border.all(color: Colors.grey[400]!)),
                        child: Column( crossAxisAlignment: CrossAxisAlignment.start, children: _parsedResultWidgets!, ),
                      ),

                  ],
                ),
              ),
            ), // End Expanded

          ],
        ),
      ),

      // --- FAB Setup (Simplified) ---
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Animated options menu
          AnimatedOpacity(
            opacity: _showFabOptions ? 1.0 : 0.0,
            duration: const Duration(milliseconds: 200),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              height: _showFabOptions ? null : 0,
              child: _showFabOptions ? Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  // ONLY show image options now
                  _buildFabOption(Icons.camera_alt, () => _pickImage(ImageSource.camera), "Camera", Colors.orange[300]!),
                  _buildFabOption(Icons.photo_library, () => _pickImage(ImageSource.gallery), "Gallery", Colors.green[300]!),
                  const SizedBox(height: 16), // Space above main FAB
                ],
              ) : null,
            ),
          ),
          // Main FAB
          FloatingActionButton(
            heroTag: 'mainFab',
            backgroundColor: _showFabOptions ? Colors.grey[600] : theme.colorScheme.primary,
            child: AnimatedRotation(
              turns: _showFabOptions ? 0.125 : 0,
              duration: const Duration(milliseconds: 200),
              child: Icon(_showFabOptions ? Icons.close : Icons.add_a_photo_outlined), // Changed icon
            ),
            onPressed: () => setState(() => _showFabOptions = !_showFabOptions),
          ),
        ],
      ),
    );
  }
} // End _ExpenseScannerPageState