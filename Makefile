TARGET = PassGen
RESOURCES = src/resources.py

srcdir = src

all: compile src/*.py src/*.ui
	pyinstaller --onefile --windowed --add-data="src/*.ui:." --add-data="templates/*.tmpl:." --name $(TARGET) src/main.py

compile: $(RESOURCES)

# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc src/*.ui icons/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(TARGET).spec build dist
	rm -rf src/__pycache__
