function test_app_flows
%TEST_APP_FLOWS Selector, escenario, apertura y reset confirmado de los Excel.
matlabDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(matlabDir);
addpath(matlabDir);
tempRoot = tempname; mkdir(tempRoot);
cleanupFolder = onCleanup(@() rmdir(tempRoot, 's')); %#ok<NASGU>
protected = {'data/IEEE118.xlsx','data/IEEE118_escenario1.xlsx','data/IEEE14.xlsx','data/IEEE300.xlsx', ...
    'resultados_IEEE118_matlab.xlsx','resultados_IEEE118_escenario1_matlab.xlsx','comparacion_escenario1.xlsx', ...
    'resultados_IEEE14_matlab.xlsx','resultados_IEEE300_matlab.xlsx','validacion_MATPOWER.xlsx'};
before = cellfun(@(p) file_snapshot(fullfile(projectRoot,p)), protected, 'UniformOutput', false);
previousFigures = findall(groot, 'Type', 'figure');
openedFiles = {};
allowReset = false;
confirmationMessages = {};
app_flows(tempRoot, @record_open, @confirm_reset);
fig = setdiff(findall(groot, 'Type', 'figure'), previousFigures);
assert(isscalar(fig));
cleanupFigure = onCleanup(@() delete(fig)); %#ok<NASGU>
drawnow;
caseDrop = findall(fig, 'Tag', 'caseSelector');
methodDrop = findall(fig, 'Tag', 'methodSelector');
fileField = findall(fig, 'Tag', 'inputFile');
assert(isscalar(caseDrop) && isscalar(methodDrop) && isscalar(fileField));
assert(strcmp(caseDrop.Value, 'IEEE-118'));
assert(all(ismember({'IEEE-14', 'IEEE-118', 'IEEE-300'}, caseDrop.Items)));
buttons = findall(fig, 'Type', 'uibutton');
runButton = buttons(contains({buttons.Text}, 'Ejecutar'));
loadButton = buttons(strcmp({buttons.Text}, 'Cargar caso'));
outageButton = findall(fig, 'Tag', 'outage26_30');
restoreButton = findall(fig, 'Tag', 'restoreBase');
resetButton = findall(fig, 'Tag', 'resetExcelResults');
assert(isscalar(resetButton) && strcmp(resetButton.Enable, 'on'));
scenarioTable = findall(fig, 'Tag', 'scenarioComparison');
branchTable = findall(fig, 'Tag', 'branchInputs');
maxField = findall(fig, 'Tag', 'maxIterations');
assert(strcmp(outageButton.Enable,'off') && strcmp(restoreButton.Enable,'off'));
assert(isempty(scenarioTable.Data));
assert(~isfile(fullfile(tempRoot,'resultados_IEEE118_matlab.xlsx')));

% Los botones abren la entrada cargada y las salidas de esta carpeta, no las
% evidencias existentes en la raíz. El abridor simulado no lanza Excel.
excelTags = {'openInputExcel', 'openScenarioInputExcel', 'openBaseResultsExcel', ...
    'openScenarioResultsExcel', 'openComparisonExcel'};
excelButtons = cellfun(@(tag) findall(fig, 'Tag', tag), excelTags, 'UniformOutput', false);
assert(all(cellfun(@isscalar, excelButtons)));
assert(strcmp(excelButtons{1}.Enable, 'on') && strcmp(excelButtons{2}.Enable, 'on'));
assert(all(cellfun(@(button) strcmp(button.Enable, 'off'), excelButtons(3:5))));
for buttonIndex = 1:2
    button = excelButtons{buttonIndex};
    button.ButtonPushedFcn(button, []);
end
assert(isequal(openedFiles, {fullfile(projectRoot,'data','IEEE118.xlsx'), ...
    fullfile(projectRoot,'data','IEEE118_escenario1.xlsx')}));

% El selector actualiza tablas y sustituye todas las trazas de cada caso.
for nBus = [14 300 118]
    choose_case(caseDrop, nBus);
    assert(strcmp(fileField.Value, fullfile(projectRoot, 'data', sprintf('IEEE%d.xlsx', nBus))));
    check_case(fig, nBus, 3);
    if nBus == 300
        assert(maxField.Value >= 30000);
        assert(strcmp(outageButton.Enable,'off'));
    end
end

% Base completa exportada antes de habilitar la intervención.
assert(strcmp(outageButton.Enable,'on'));
assert(isfile(fullfile(tempRoot,'resultados_IEEE118_matlab.xlsx')));
assert(strcmp(excelButtons{3}.Enable, 'on'));
assert(strcmp(excelButtons{4}.Enable, 'off') && strcmp(excelButtons{5}.Enable, 'off'));
excelButtons{3}.ButtonPushedFcn(excelButtons{3}, []);
assert(strcmp(openedFiles{end}, fullfile(tempRoot,'resultados_IEEE118_matlab.xlsx')));
baseSummary = summary_table(fig).Data;
baseBranches = branchTable.Data;
assert(all(baseBranches.STATUS == 1));
outageButton.ButtonPushedFcn(outageButton, []);
drawnow;
assert(strcmp(outageButton.Enable,'off') && strcmp(restoreButton.Enable,'on'));
assert(strcmp(caseDrop.Value,'Personalizado'));
assert(strcmp(fileField.Value,fullfile(projectRoot,'data','IEEE118_escenario1.xlsx')));
assert(branchTable.Data.STATUS(38) == 0 && sum(branchTable.Data.STATUS ~= 0) == 185);
expected = baseBranches; expected.STATUS(38) = 0;
assert(isequaln(branchTable.Data,expected), 'Cambió más que el estado de la línea.');
assert(height(branchTable.StyleConfigurations) >= 2, 'Falta resaltado de fila/celda.');
styles = branchTable.StyleConfigurations.Style;
if iscell(styles), styles = [styles{:}]; end
assert(all(arrayfun(@(style) isequal(style.FontColor, [0 0 0]), styles)), ...
    'El texto resaltado debe ser negro, incluso con el tema oscuro.');
assert(isequal(styles(1).BackgroundColor, [1 .94 .65]) && ...
    isequal(styles(2).BackgroundColor, [1 .75 .25]), 'Deben conservarse los fondos amarillos.');
check_case(fig,118,3);
comparison = scenarioTable.Data;
assert(height(comparison) == 11);
assert(isequal(comparison{[5,9,10],{'Caso_base','Escenario'}}, [3 6;3 4;757 909]));
assert(abs(comparison.Escenario(8)-165.897686) < 1e-5);
globalTable = findall(fig,'Tag','globalFlowChanges');
activeTable = findall(fig,'Tag','activeFlowChanges');
assert(height(globalTable.Data) == 5 && height(activeTable.Data) == 5);
assert(globalTable.Data.Desde(1) == 26 && globalTable.Data.Hasta(1) == 30);
assert(globalTable.Data.Delta_pct(1) == -100);
scenarioAxes = findall(fig,'Tag','scenarioVoltage');
assert(numel(findobj(scenarioAxes,'Type','line')) == 2);
assert(isfile(fullfile(tempRoot,'resultados_IEEE118_escenario1_matlab.xlsx')));
comparisonFile = fullfile(tempRoot,'comparacion_escenario1.xlsx');
assert(isfile(comparisonFile));
assert(all(cellfun(@(button) strcmp(button.Enable, 'on'), excelButtons)));
excelButtons{1}.ButtonPushedFcn(excelButtons{1}, []);
assert(strcmp(openedFiles{end}, fullfile(projectRoot,'data','IEEE118_escenario1.xlsx')));
for buttonIndex = 4:5
    button = excelButtons{buttonIndex};
    button.ButtonPushedFcn(button, []);
end
assert(isequal(openedFiles(end-1:end), {fullfile(tempRoot,'resultados_IEEE118_escenario1_matlab.xlsx'), comparisonFile}));
saved = readtable(comparisonFile,'Sheet','comparacion','VariableNamingRule','preserve');
saved.Variable = string(saved.Variable);
assert(isequaln(saved,comparison));
for method = {'NR','GS','FDLF'}
    saved = readtable(fullfile(tempRoot,'resultados_IEEE118_escenario1_matlab.xlsx'), ...
        'Sheet',[method{1},'_branch']);
    assert(all(saved{38,{'P_from_MW','Q_from_MVAr','P_to_MW','Q_to_MVAr'}} == 0));
end

% Volver recupera exactamente el snapshot base sin recalcular.
restoreButton.ButtonPushedFcn(restoreButton, []);
assert(strcmp(outageButton.Enable,'on') && strcmp(restoreButton.Enable,'off'));
assert(isequaln(branchTable.Data,baseBranches));
assert(isequaln(summary_table(fig).Data,baseSummary));
assert(strcmp(caseDrop.Value,'IEEE-118'));
excelButtons{1}.ButtonPushedFcn(excelButtons{1}, []);
assert(strcmp(openedFiles{end}, fullfile(projectRoot,'data','IEEE118.xlsx')));

% Ediciones y parámetros invalidan resultados y comparación.
limits = findall(fig,'Tag','tolerance');
limits.Value = 1e-7; limits.ValueChangedFcn(limits,[]);
assert(strcmp(outageButton.Enable,'off') && isempty(scenarioTable.Data));
assert(isempty(summary_table(fig).Data));
% Invalidar las vistas no borra ni bloquea los Excel ya guardados.
assert(all(cellfun(@(button) strcmp(button.Enable, 'on'), excelButtons)));
limits.Value = 1e-8; limits.ValueChangedFcn(limits,[]);
runButton.ButtonPushedFcn(runButton,[]);
assert(strcmp(outageButton.Enable,'on'));
% También se bloquean ediciones programáticas sin callback.
originalComparison = file_bytes(comparisonFile);
data = branchTable.Data; data.STATUS(1) = 0; branchTable.Data = data;
outageButton.ButtonPushedFcn(outageButton,[]);
assert(strcmp(outageButton.Enable,'off') && isempty(scenarioTable.Data));
assert(isequal(file_bytes(comparisonFile),originalComparison));
choose_case(caseDrop,118);
busTable = findall(fig,'Tag','busInputs');
data = busTable.Data; data.PD(1) = data.PD(1)+1; busTable.Data = data;
busTable.CellEditCallback(busTable,[]);
assert(strcmp(outageButton.Enable,'off') && isempty(summary_table(fig).Data));
choose_case(caseDrop,118);
qCheck = findall(fig,'Tag','enforceQLimits');
qCheck.Value = true; qCheck.ValueChangedFcn(qCheck,[]);
assert(strcmp(outageButton.Enable,'off'));
qCheck.Value = false; qCheck.ValueChangedFcn(qCheck,[]);
maxField.Value = 1; maxField.ValueChangedFcn(maxField,[]);
runButton.ButtonPushedFcn(runButton,[]);
assert(strcmp(outageButton.Enable,'off') && ~all(summary_table(fig).Data.Convergio));
maxField.Value = 1000; maxField.ValueChangedFcn(maxField,[]);

% El selector conserva el método elegido; un método solo no habilita salida.
methodDrop.Value = 'Newton-Raphson';
choose_case(caseDrop, 14);
check_case(fig, 14, 1);
assert(strcmp(outageButton.Enable,'off'));

% Un Excel propio no conserva resultados anteriores ni se confunde con incluido.
customFile = fullfile(tempRoot,'custom.xlsx');
copyfile(fullfile(projectRoot, 'data', 'IEEE14.xlsx'), customFile);
fileField.Value = customFile;
loadButton.ButtonPushedFcn(loadButton, []);
assert(strcmp(caseDrop.Value, 'Personalizado'));
excelButtons{1}.ButtonPushedFcn(excelButtons{1}, []);
assert(strcmp(openedFiles{end}, customFile));
summary = summary_table(fig);
assert(isempty(summary.Data) && isempty(scenarioTable.Data));
assert(isempty(findall(fig, 'Type', 'line')));
runButton.ButtonPushedFcn(runButton, []);
check_case(fig, 14, 1);

% Cargar un incluido vuelve a sincronizar selector, sin habilitar con NR solo.
fileField.Value = fullfile(projectRoot, 'data', 'IEEE118.xlsx');
loadButton.ButtonPushedFcn(loadButton, []);
assert(strcmp(caseDrop.Value, 'IEEE-118'));
assert(isempty(summary.Data) && isempty(findall(fig, 'Type', 'line')));
runButton.ButtonPushedFcn(runButton, []);
check_case(fig, 118, 1);
assert(strcmp(outageButton.Enable,'off'));
% Reset desde el escenario: cancelar no cambia archivos ni el snapshot base.
methodDrop.Value = 'Todos';
choose_case(caseDrop, 118);
outageButton.ButtonPushedFcn(outageButton, []);
assert(strcmp(restoreButton.Enable, 'on') && height(scenarioTable.Data) == 11);
resultNames = {'resultados_IEEE118_matlab.xlsx','resultados_IEEE118_escenario1_matlab.xlsx', ...
    'comparacion_escenario1.xlsx','resultados_IEEE14_matlab.xlsx', ...
    'resultados_IEEE300_matlab.xlsx','validacion_MATPOWER.xlsx'};
resultPaths = cellfun(@(name) fullfile(tempRoot,name), resultNames, 'UniformOutput', false);
for fileIndex = 4:6
    copyfile(fullfile(projectRoot,'data','IEEE14.xlsx'), resultPaths{fileIndex});
end
unrelatedFile = fullfile(tempRoot,'no_borrar.xlsx');
copyfile(customFile, unrelatedFile);
savedFiles = cellfun(@file_bytes, resultPaths, 'UniformOutput', false);
savedSummary = summary_table(fig).Data;
savedComparison = scenarioTable.Data;
savedBranches = branchTable.Data;
savedInput = fileField.Value;
savedMaxIterations = maxField.Value;
resetButton.ButtonPushedFcn(resetButton, []);
assert(numel(confirmationMessages) == 1 && contains(confirmationMessages{1}, tempRoot));
assert(all(cellfun(@(name) contains(confirmationMessages{1},name), resultNames)));
assert(isequal(savedFiles, cellfun(@file_bytes, resultPaths, 'UniformOutput', false)));
assert(isequaln(summary_table(fig).Data, savedSummary) && isequaln(scenarioTable.Data, savedComparison));
assert(strcmp(restoreButton.Enable, 'on') && strcmp(resetButton.Enable, 'on'));

% Confirmar borra SOLO las seis salidas conocidas en la carpeta elegida.
allowReset = true;
resetButton.ButtonPushedFcn(resetButton, []);
assert(numel(confirmationMessages) == 2);
assert(~any(cellfun(@isfile, resultPaths)));
assert(isfile(customFile) && isfile(unrelatedFile));
assert(isempty(summary_table(fig).Data) && isempty(scenarioTable.Data));
assert(isempty(globalTable.Data) && isempty(activeTable.Data));
assert(isempty(findall(fig, 'Type', 'line')));
assert(strcmp(outageButton.Enable, 'off') && strcmp(restoreButton.Enable, 'off'));
assert(all(cellfun(@(button) strcmp(button.Enable, 'off'), excelButtons(3:5))));
assert(strcmp(excelButtons{1}.Enable, 'on') && strcmp(excelButtons{2}.Enable, 'on'));
assert(strcmp(fileField.Value, savedInput) && isequaln(branchTable.Data, savedBranches));
assert(maxField.Value == savedMaxIterations && strcmp(methodDrop.Value, 'Todos'));
assert(strcmp(findall(fig,'Tag','calculationStatus').Text, 'Resultados reiniciados'));
% Es seguro repetir el reset cuando ya no quedan archivos.
resetButton.ButtonPushedFcn(resetButton, []);
assert(numel(confirmationMessages) == 3 && strcmp(resetButton.Enable, 'on'));

% Una entrada propia nunca se borra aunque tenga el nombre de una salida.
protectedInput = resultPaths{4};
copyfile(customFile, protectedInput);
fileField.Value = protectedInput;
loadButton.ButtonPushedFcn(loadButton, []);
protectedBytes = file_bytes(protectedInput);
resetButton.ButtonPushedFcn(resetButton, []);
assert(isfile(protectedInput) && isequal(file_bytes(protectedInput), protectedBytes));
assert(numel(confirmationMessages) == 3, 'El reset debe bloquearse antes de confirmar si afectaría una entrada.');
assert(strcmp(findall(fig,'Tag','calculationStatus').Text, 'Error en el reset'));
after = cellfun(@(p) file_snapshot(fullfile(projectRoot,p)), protected, 'UniformOutput', false);
assert(isequal(before,after), 'Las pruebas no deben modificar entradas ni salidas del proyecto.');
fprintf('test_app_flows: selector, escenario, apertura y reset seguro de Excel OK.\n');

    function record_open(filename)
        assert(isfile(filename), 'El botón debe apuntar a un archivo existente.');
        openedFiles{end+1} = filename;
    end

    function confirmed = confirm_reset(message)
        confirmationMessages{end+1} = message;
        assert(strcmp(resetButton.Enable, 'off') && strcmp(runButton.Enable, 'off'));
        assert(all(cellfun(@(button) strcmp(button.Enable, 'off'), excelButtons)));
        confirmed = allowReset;
    end
end

function choose_case(drop, nBus)
drop.Value = sprintf('IEEE-%d', nBus);
drop.ValueChangedFcn(drop, []);
end

function summary = summary_table(fig)
tables = findall(fig, 'Type', 'uitable');
summary = tables(arrayfun(@(t) strcmp(t.Parent.Parent.Title, 'Comparación'), tables));
assert(isscalar(summary));
end

function check_case(fig, nBus, nMethods)
drawnow;
busTable = findall(fig,'Tag','busInputs');
assert(isscalar(busTable) && height(busTable.Data) == nBus);
summary = summary_table(fig);
assert(height(summary.Data) == nMethods && all(summary.Data.Convergio));
if nMethods == 1, assert(strcmp(summary.Data.Metodo, 'Newton-Raphson')); end
axesList = findall(fig, 'Type', 'axes');
convAxes = axesList(arrayfun(@(a) strcmp(a.YLabel.String, 'Error máximo (pu)'), axesList));
assert(isscalar(convAxes) && strcmp(convAxes.YScale, 'log'));
lines = findobj(convAxes, 'Type', 'line');
assert(numel(lines) == nMethods);
assert(convAxes.XLim(2) == max(summary.Data.Iteraciones));
for k = 1:numel(lines)
    assert(all(lines(k).YData > convAxes.YLim(1)) && all(lines(k).YData < convAxes.YLim(2)));
end
profileAxes = axesList(arrayfun(@(a) ismember(a.Tag, {'voltageProfile','angleProfile'}), axesList));
assert(numel(profileAxes) == 2);
for k = 1:numel(profileAxes)
    lines = findobj(profileAxes(k), 'Type', 'line');
    assert(numel(lines) == nMethods);
    assert(all(arrayfun(@(line) numel(line.XData) == nBus, lines)));
end
end

function snapshot = file_snapshot(filename)
% También protege la ausencia de salidas tras limpiar el repositorio.
snapshot = struct('exists', isfile(filename), 'bytes', []);
if snapshot.exists, snapshot.bytes = file_bytes(filename); end
end

function bytes = file_bytes(filename)
fid = fopen(filename,'rb'); assert(fid ~= -1);
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
bytes = fread(fid,inf,'*uint8');
end
