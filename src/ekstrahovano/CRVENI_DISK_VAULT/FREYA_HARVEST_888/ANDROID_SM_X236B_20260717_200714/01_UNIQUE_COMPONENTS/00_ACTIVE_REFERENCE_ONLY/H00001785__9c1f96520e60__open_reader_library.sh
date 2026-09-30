#!/data/data/com.termux/files/usr/bin/bash
LIB="/storage/2983-487E/READING_LIBRARY_HUMAN_GATE"
echo "OPEN_READER_LIBRARY"
echo "LIB=$LIB"
termux-open "$LIB" 2>/dev/null || echo "OPEN_FOLDER_FAILED_USE_MY_FILES_MANUALLY"
