function capture_scenario_gui(outputDir)
%CAPTURE_SCENARIO_GUI Capturas reales del flujo interactivo, sin tocar resultados.
% addpath('tools'); capture_scenario_gui;
% Las corridas se exportan a una carpeta temporal que se elimina al terminar.
% Estas imágenes NO acreditan el video continuo ni voces del grupo.
root = fileparts(fileparts(mfilename('fullpath')));
if nargin < 1, outputDir = fullfile(root,'escenario1_assets'); end
if ~isfolder(outputDir), mkdir(outputDir); end
addpath(fullfile(root,'matlab'));
temporary = tempname; mkdir(temporary);
fig = app_flows(temporary);
cleanup = onCleanup(@() close_capture(fig,temporary)); %#ok<NASGU>
fig.Position = [20 20 1600 1000];
if isprop(fig,'Theme'), fig.Theme = 'light'; end
mainGrid = fig.Children(1);
mainGrid.RowHeight = {38,38,38,38,46,38,260,'1x'};
branchTable = findall(fig,'Tag','branchInputs');
run = findall(fig,'Type','uibutton'); run = run(contains({run.Text},'Ejecutar'));
outage = findall(fig,'Tag','outage26_30');
compareTable = findall(fig,'Tag','scenarioComparison');
compareTable.ColumnWidth = {265,105,105,105};
assert(strcmp(outage.Enable,'off'));
drawnow; pause(1);
exportapp(fig,fullfile(outputDir,'gui_estado_inicial.png'));
run.ButtonPushedFcn(run,[]);
assert(strcmp(outage.Enable,'on'));
summary = find_summary(fig); baseSummary = summary.Data;
tabs = findall(fig,'Type','uitab');
branchTab = tabs(strcmp({tabs.Title},'Ramas'));
branchTab.Parent.SelectedTab = branchTab;
drawnow; pause(1);
scroll(branchTable,'row',38);
drawnow; pause(2);
exportapp(fig,fullfile(outputDir,'gui_caso_base.png'));
outage.ButtonPushedFcn(outage,[]);
assert(strcmp(outage.Enable,'off'));
assert(branchTable.Data.STATUS(38) == 0 && height(compareTable.Data) == 11);
scenarioSummary = summary.Data;
drawnow; pause(1);
exportapp(fig,fullfile(outputDir,'gui_salida_26_30.png'));
meta = struct('timestampUTC',char(datetime('now','TimeZone','UTC', ...
    'Format',"yyyy-MM-dd'T'HH:mm:ss'Z'")), 'matlabVersion',version, ...
    'callbackSequence',{{'Ejecutar métodos (Todos, IEEE118 base)','Retirar línea 26–30'}}, ...
    'base',table2struct(baseSummary),'scenario',table2struct(scenarioSummary), ...
    'comparison',table2struct(compareTable.Data),'temporaryExportsOnly',true, ...
    'recordingStatus','Capturas técnicas estáticas; no son video continuo ni acreditan voces');
fid = fopen(fullfile(outputDir,'captura_GUI_escenario1.json'),'w','n','UTF-8');
assert(fid ~= -1);
closeFile = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(meta,'PrettyPrint',true));
fprintf('Capturas GUI base y salida listas: %s (exportaciones temporales).\n',outputDir);
end

function summary = find_summary(fig)
tables = findall(fig,'Type','uitable');
summary = tables(arrayfun(@(t) istable(t.Data) && ...
    ismember('ErrorFinalPU',t.Data.Properties.VariableNames),tables));
assert(isscalar(summary));
end

function close_capture(fig,folder)
if isvalid(fig), delete(fig); end
if isfolder(folder), rmdir(folder,'s'); end
end
