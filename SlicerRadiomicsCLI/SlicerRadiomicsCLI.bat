SET PYTHON_INTERPRETER=python-real.exe
REM Check if python-real exists: this is the case of installed version of Slicer
where /q %PYTHON_INTERPRETER%
IF ERRORLEVEL 1 (
	REM python-real does not exist! Maybe running from a build-tree? in that case, use python.exe
	SET PYTHON_INTERPRETER=python.exe
)

%PYTHON_INTERPRETER% %~dp0SlicerRadiomicsCLIScript %*
