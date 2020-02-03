SOURCES := $(wildcard *.vasm)
OUTPUTS := $(patsubst %.vasm,%.bin,$(SOURCES)) 

all: $(OUTPUTS) 

%.bin: %.vasm
	../vasm_assembler $<

clean:
	rm -f $(OUTPUTS)
