#!/data/data/com.termux/files/usr/bin/bash
TEST="/storage/2983-487E/READING_LIBRARY_HUMAN_GATE/03_TXT_MD/HUMAN_GATE_TEST_READER.txt"
echo "OPEN_READER_TEST"
echo "TEST=$TEST"
termux-open "$TEST" 2>/dev/null || echo "OPEN_TEST_FAILED"
