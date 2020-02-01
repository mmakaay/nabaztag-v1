all:
	rm -f wiebelen.raw
	rm -f wiebelen.vox
	rm -f wiebelen.wav
	rm -f wiebelen.pcm
	rm -f wiebelen2.wav
	#ffmpeg -i wiebelen.mp3 -to 00:00:10 -ac 1 -ar 16000 -f u16be -acodec pcm_u16be wiebelen.pcm
	#ffmpeg -i wiebelen.mp3 -to 00:00:10 -ac 1 -ar 16000 -f u8 -acodec pcm_u8 wiebelen.raw
	ffmpeg -i wiebelen.mp3 -to 00:00:10 -ac 1 -ar 8000 -f u8 -acodec pcm_u8 wiebelen.raw
	ffmpeg -ac 1 -ar 8000 -f u8 -acodec pcm_u8 -i wiebelen.raw wiebelen.wav
	vox -b 8 wiebelen.raw wiebelen.vox
	sox wiebelen.vox -b 8 -r 8000 wiebelen2.wav

	cp wiebelen.vox ..

    # Works, but very ugly sound
	#ffmpeg -i wiebelen.mp3 -to 00:02:00 -ac 1 -ar 16000 -f u16be -acodec pcm_u16le wiebelen.raw
	#vox -b 16 wiebelen.raw wiebelen.vox
