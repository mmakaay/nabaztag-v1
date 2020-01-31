SOURCES := $(wildcard *.basm)
OUTPUTS := $(patsubst %.basm,%.bin,$(SOURCES)) 

clean:
	rm $(OUTPUTS)

all: $(OUTPUTS) 

%.bin: %.basm
	PYTHONPATH=.. ./bassemble $<
