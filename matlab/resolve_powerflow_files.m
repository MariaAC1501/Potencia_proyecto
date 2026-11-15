function [inputFile, outputFile] = resolve_powerflow_files(inputFile, outputFile)
%RESOLVE_POWERFLOW_FILES Resuelve los defaults de main sin escribir archivos.
projectRoot = fileparts(fileparts(mfilename('fullpath')));
if nargin < 1 || isempty(inputFile) || strlength(string(inputFile)) == 0
    inputFile = fullfile(projectRoot, 'data', 'IEEE118.xlsx');
end
if nargin < 2 || isempty(outputFile) || strlength(string(outputFile)) == 0
    [~, caseName] = fileparts(inputFile);
    outputFile = fullfile(projectRoot, ['resultados_', char(caseName), '_matlab.xlsx']);
end
end
