import re

# Read Kira.jsx
with open(r'e:\VSCODE\NineToFive\frontend\src\pages\Kira.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# New smooth TTS function
new_function = '''    // =================================================================================
    // 4. SMOOTH TTS STREAMING (No pauses at punctuation)
    // =================================================================================
    const handleTTSStreaming = (textChunk) => {
        sentenceBufferRef.current += textChunk;

        // SMOOTH STRATEGY: Accumulate words, speak in natural chunks of ~10-15 words
        // This avoids awkward pauses at commas and creates flowing speech
        const words = sentenceBufferRef.current.split(/\\s+/);

        // Speak when we have enough words (10-15) OR hit a final sentence ending
        const hasFinalEnding = /[.!?।]\\s*$/.test(sentenceBufferRef.current);

        if (words.length >= 10 || (hasFinalEnding && words.length >= 5)) {
            // Determine how many words to speak
            let wordsToSpeak;

            if (hasFinalEnding) {
                // Speak everything up to and including the final punctuation
                wordsToSpeak = words.length;
            } else {
                // Speak 10-12 words, keeping a few in buffer for smooth continuation
                wordsToSpeak = Math.min(12, words.length - 3);
            }

            if (wordsToSpeak > 0) {
                const textToSpeak = words.slice(0, wordsToSpeak).join(' ');
                const remainder = words.slice(wordsToSpeak).join(' ');

                if (textToSpeak.trim().length > 0) {
                    speakText(textToSpeak.trim());
                }

                sentenceBufferRef.current = remainder;
            }
        }
    };'''

# Pattern to match the old handleTTSStreaming function
pattern = r'    // =================================================================================\s+// 4\. AGGRESSIVE TTS STREAMING.*?    };'

# Replace
new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Write back
with open(r'e:\VSCODE\NineToFive\frontend\src\pages\Kira.jsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully updated TTS to smooth word-accumulation strategy!")
