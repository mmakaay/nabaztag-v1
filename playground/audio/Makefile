all:
	rm -f wiebelen.vox
	rm -f wiebelen.raw
	#ffmpeg -i wiebelen.wav -c 1 -ar 16000 -f u16 -acodec pcm_u16 wiebelen.raw
	ffmpeg -i wiebelen.wav -c 1 -ar 16000 -f u16be -acodec pcm_u16be wiebelen.raw
	vox -b 8 wiebelen.raw wiebelen.vox
	cp wiebelen.vox ..
	./create_midi.py && cp my.mid ..

