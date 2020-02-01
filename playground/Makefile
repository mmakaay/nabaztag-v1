SOURCES := $(wildcard *.basm)
OUTPUTS := $(patsubst %.basm,%.bin,$(SOURCES)) 

all: $(OUTPUTS) 

%.bin: %.basm
	../basm_assembler $<

clean:
	rm -f $(OUTPUTS)
