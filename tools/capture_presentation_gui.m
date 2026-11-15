function capture_presentation_gui(outputDir, projectRoot)
% Capture the real app; presentation-only styling is applied in memory.
addpath(fullfile(projectRoot, 'matlab'));
temporary = tempname; mkdir(temporary);
cleanupFolder = onCleanup(@() rmdir(temporary,'s')); %#ok<NASGU>
app_flows(temporary);
figs = findall(groot, 'Type', 'figure');
fig = figs(strcmp({figs.Name}, 'Flujos de potencia - MATLAB'));
assert(isscalar(fig), 'Expected exactly one app_flows figure.');
cleanup = onCleanup(@() delete(fig)); %#ok<NASGU>
fig.Position = [20 20 2000 1100];
if isprop(fig, 'Theme'), fig.Theme = 'light'; end
objects = findall(fig);
for k = 1:numel(objects)
    if isprop(objects(k), 'FontSize'), objects(k).FontSize = 20; end
end
mainGrid = fig.Children(1);
mainGrid.RowHeight = {48, 48, 48, 48, 48, 48, 245, '1x'};
outage = findall(fig,'Tag','outage26_30');
outage.Parent.ColumnWidth = {360,300,'1x'};
mainGrid.ColumnWidth = {220, '1x', 230, 430};
tables = findall(fig, 'Type', 'uitable');
for k = 1:numel(tables)
    if ~isempty(tables(k).Data)
        tables(k).ColumnWidth = repmat({115}, 1, width(tables(k).Data));
    end
end
buttons = findall(fig, 'Type', 'uibutton');
loadButton = buttons(strcmp({buttons.Text}, 'Cargar caso'));
loadButton.ButtonPushedFcn(loadButton, []);
labels = findall(fig, 'Type', 'uilabel');
status = labels(startsWith(string({labels.Text}), 'Cargado:'));
assert(isscalar(status), 'The real load callback did not complete.');
status.FontSize = 16;
status.WordWrap = 'on';
drawnow; pause(3);
exportapp(fig, fullfile(outputDir, 'gui_caso.png'));

% Invoke the original callback, with the original Todos/default settings.
runButton = buttons(contains(string({buttons.Text}), 'Ejecutar'));
assert(isscalar(runButton));
runButton.ButtonPushedFcn(runButton, []);
assert(strcmp(status.Text, 'Cálculo terminado'), 'Calculation callback failed.');
summary = tables(arrayfun(@(t) istable(t.Data) && ...
    ismember('ErrorFinalPU', t.Data.Properties.VariableNames), tables));
assert(isscalar(summary) && height(summary.Data) == 3, 'Three real methods required.');
summary.ColumnWidth = repmat({160},1,width(summary.Data));
summary.Parent.ColumnWidth = {'1.15x', '1x'};
axesList = findall(fig, 'Type', 'axes');
for k = 1:numel(axesList), axesList(k).FontSize = 17; end
legends = findall(fig, 'Type', 'legend');
for k = 1:numel(legends), legends(k).FontSize = 15; end
drawnow; pause(3);
exportapp(fig, fullfile(outputDir, 'gui_ejecutado.png'));

% Pixel bounds refer to the actual laid-out UI, not hand-drawn replacements.
tabs = findall(fig, 'Type', 'uitab');
comparisonTab = tabs(strcmp({tabs.Title}, 'Comparación'));
profileTab = tabs(strcmp({tabs.Title}, 'Perfil de tensión'));
resultTabs = comparisonTab.Parent;
fileField = findall(fig, 'Type', 'uieditfield', '-and', 'Value', ...
    fullfile(projectRoot, 'data', 'IEEE118.xlsx'));
assert(isscalar(fileField));
filePos = getpixelposition(fileField, true);
methodDrop = findall(fig, 'Type', 'uidropdown', 'Tag', 'methodSelector');
methodPos = getpixelposition(methodDrop, true);
runPos = getpixelposition(runButton, true);
metadata = struct;
metadata.figure_size = fig.Position(3:4);
metadata.coordinate_system = 'MATLAB figure pixels, bottom-left; [x y width height]';
metadata.crops.gui_archivo = [10, filePos(2)-5, 1980, filePos(4)+10];
metadata.crops.gui_parametros = [10, runPos(2)-5, 1980, ...
    methodPos(2)+methodPos(4)-runPos(2)+10];
metadata.crops.gui_comparacion = getpixelposition(resultTabs, true);
metadata.results = table2struct(summary.Data);
metadata.loaded_file = fileField.Value;
metadata.callback = 'Original ButtonPushedFcn: Cargar caso; Ejecutar métodos (Todos)';
metadata.options = struct('tolerance', 1e-8, 'relaxation', 1.5, ...
    'enforceQLimits', false, 'maxIterations', []);
numericFields = findall(fig, 'Type', 'uinumericeditfield');
for k = 1:numel(numericFields)
    if numericFields(k).Value >= 1000
        metadata.options.maxIterations = numericFields(k).Value;
    end
end
resultTabs.SelectedTab = profileTab;
drawnow; pause(3);
exportapp(fig, fullfile(outputDir, 'gui_perfil.png'));
fid = fopen(fullfile(outputDir, 'capture_gui_metadata.json'), 'w', 'n', 'UTF-8');
assert(fid ~= -1);
fwrite(fid, jsonencode(metadata, PrettyPrint=true), 'char');
fclose(fid);
end
