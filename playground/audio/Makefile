all:
	rm -f wiebelen.vox wiebelen.raw
	ffmpeg -i wiebelen.mp3 -to 00:00:05 -ac 1 -ar 16000 -f u16be -acodec pcm_u16le wiebelen.raw
	vox -b 16 wiebelen.raw wiebelen.vox
