SOURCES := $(wildcard *.basm)
OUTPUTS := $(patsubst %.basm,%.bin,$(SOURCES)) 

all: $(OUTPUTS) 

%.bin: %.basm
	PYTHONPATH=.. ./bassemble $<

clean:
	rm -f $(OUTPUTS)
