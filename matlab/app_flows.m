function fig = app_flows(outputFolder, openExcel, confirmReset)
%APP_FLOWS Resuelve la red base y permite retirar después la línea 26–30.
% Ejecutar con: addpath('matlab'); app_flows
% app_flows(carpetaSalida) aísla las exportaciones, por ejemplo en las pruebas.
% Los argumentos opcionales openExcel y confirmReset permiten probar la
% apertura y la confirmación del borrado sin abrir Excel ni diálogos.

matlabDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(matlabDir);
addpath(matlabDir);
if nargin < 2 || isempty(openExcel), openExcel = @winopen; end
validateattributes(openExcel, {'function_handle'}, {'scalar'}, mfilename, 'openExcel');
if nargin < 3 || isempty(confirmReset), confirmReset = @confirm_excel_reset; end
validateattributes(confirmReset, {'function_handle'}, {'scalar'}, mfilename, 'confirmReset');
if nargin < 1 || isempty(outputFolder), outputFolder = projectRoot; end
if ~isfolder(outputFolder), mkdir(outputFolder); end
[~, folderInfo] = fileattrib(outputFolder);
outputFolder = folderInfo.Name;
caseLabels = {'IEEE-14', 'IEEE-118', 'IEEE-300'};
caseFiles = cellfun(@(n) fullfile(projectRoot, 'data', ['IEEE', n, '.xlsx']), ...
    {'14', '118', '300'}, 'UniformOutput', false);
defaultFile = caseFiles{2};
state.inputFile = defaultFile;
state.caseSelection = 'IEEE-118';
state.caseData = load_case_excel(defaultFile);
defaultMaxIterations = recommended_max_iterations(state.caseData, 1000);
state.results = [];
state.base = [];
state.analysis = [];
state.phase = 'case';
state.busy = false;
referenceCase = state.caseData;
scenarioFile = fullfile(projectRoot, 'data', 'IEEE118_escenario1.xlsx');
baseOutput = fullfile(outputFolder, 'resultados_IEEE118_matlab.xlsx');
scenarioOutput = fullfile(outputFolder, 'resultados_IEEE118_escenario1_matlab.xlsx');
comparisonOutput = fullfile(outputFolder, 'comparacion_escenario1.xlsx');
resultFiles = {baseOutput, scenarioOutput, comparisonOutput, ...
    fullfile(outputFolder, 'resultados_IEEE14_matlab.xlsx'), ...
    fullfile(outputFolder, 'resultados_IEEE300_matlab.xlsx'), ...
    fullfile(outputFolder, 'validacion_MATPOWER.xlsx')};

fig = uifigure('Name', 'Flujos de potencia - MATLAB', 'Position', [80 60 1400 850]);
mainGrid = uigridlayout(fig, [8 4]);
mainGrid.RowHeight = {35, 35, 35, 35, 38, 38, '1x', 260};
mainGrid.ColumnWidth = {130, '1x', 130, 160};

uilabel(mainGrid, 'Text', 'Caso visualizado:', 'HorizontalAlignment', 'right');
caseFileGrid = uigridlayout(mainGrid, [1 2]);
caseFileGrid.Layout.Column = 2;
caseFileGrid.ColumnWidth = {140, '1x'};
caseFileGrid.Padding = [0 0 0 0];
caseDrop = uidropdown(caseFileGrid, 'Items', [caseLabels, {'Personalizado'}], ...
    'Value', state.caseSelection, 'Tag', 'caseSelector', ...
    'Tooltip', 'Selecciona un caso para cargarlo y actualizar sus resultados.', ...
    'ValueChangedFcn', @select_case);
fileField = uieditfield(caseFileGrid, 'text', 'Value', defaultFile, ...
    'Tag', 'inputFile', 'Tooltip', 'Archivo Excel del caso. También puedes cargar un archivo propio.');
selectButton = uibutton(mainGrid, 'Text', 'Seleccionar...');
selectButton.Layout.Column = 3; selectButton.ButtonPushedFcn = @select_file;
loadButton = uibutton(mainGrid, 'Text', 'Cargar caso');
loadButton.Layout.Column = 4; loadButton.ButtonPushedFcn = @load_file;

uilabel(mainGrid, 'Text', 'Método:', 'HorizontalAlignment', 'right');
methodDrop = uidropdown(mainGrid, 'Items', {'Todos','Newton-Raphson','Gauss-Seidel','Desacoplado rápido'}, 'Value', 'Todos', 'Tag', 'methodSelector');
methodDrop.Layout.Column = 2;
uilabel(mainGrid, 'Text', 'Tolerancia:');
tolField = uieditfield(mainGrid, 'numeric', 'Value', 1e-8, 'Limits', [1e-12 1e-2]);
tolField.Layout.Column = 4; tolField.Tag = 'tolerance';

uilabel(mainGrid, 'Text', 'Máx. iteraciones:', 'HorizontalAlignment', 'right');
maxField = uieditfield(mainGrid, 'numeric', 'Value', defaultMaxIterations, 'Limits', [1 1000000], 'RoundFractionalValues', true);
maxField.Layout.Column = 2; maxField.Tag = 'maxIterations';
uilabel(mainGrid, 'Text', 'Relajación GS:');
relaxField = uieditfield(mainGrid, 'numeric', 'Value', 1.5, 'Limits', [0.1 1.9]);
relaxField.Layout.Column = 4; relaxField.Tag = 'relaxation';

runButton = uibutton(mainGrid, 'Text', '▶ Ejecutar métodos', 'FontWeight', 'bold');
runButton.Layout.Row = 4; runButton.Layout.Column = [1 2]; runButton.ButtonPushedFcn = @run_case;
qCheck = uicheckbox(mainGrid, 'Text', 'Aplicar límites Q');
qCheck.Layout.Row = 4; qCheck.Layout.Column = 3; qCheck.Tag = 'enforceQLimits';
statusLabel = uilabel(mainGrid, 'Text', 'Listo');
statusLabel.Layout.Row = 4; statusLabel.Layout.Column = 4;
statusLabel.WordWrap = 'on'; statusLabel.Tag = 'calculationStatus';

workflowGrid = uigridlayout(mainGrid, [1 3]);
workflowGrid.Layout.Row = 5; workflowGrid.Layout.Column = [1 4];
workflowGrid.ColumnWidth = {240, 200, '1x'}; workflowGrid.Padding = [0 0 0 0];
outageButton = uibutton(workflowGrid, 'Text', 'Retirar línea 26–30', ...
    'Tag', 'outage26_30', 'Enable', 'off', 'FontWeight', 'bold', ...
    'ButtonPushedFcn', @run_outage, ...
    'Tooltip', 'Primero ejecute IEEE-118 sin editar, con Todos, tolerancia <=1e-8 y límites Q desactivados.');
restoreButton = uibutton(workflowGrid, 'Text', 'Volver al caso base', ...
    'Tag', 'restoreBase', 'Enable', 'off', 'ButtonPushedFcn', @restore_base);
workflowLabel = uilabel(workflowGrid, 'Text', ...
    '1. Ejecute IEEE-118 con Todos.  2. Retire la línea.  3. Revise la comparación.', ...
    'Tag', 'workflowStatus', 'WordWrap', 'on');
workflowLabel.Tooltip = ['Excel de salida: ', outputFolder];

excelGrid = uigridlayout(mainGrid, [1 7]);
excelGrid.Layout.Row = 6; excelGrid.Layout.Column = [1 4];
excelGrid.ColumnWidth = {130, '1x', '1x', '1x', '1x', '1x', 190};
excelGrid.Padding = [0 0 0 0];
uilabel(excelGrid, 'Text', 'Abrir Excel:', 'HorizontalAlignment', 'right');
excelLabels = {'Entrada actual', 'Entrada 26–30', 'Resultados base', 'Resultados 26–30', 'Comparación'};
excelTags = {'openInputExcel', 'openScenarioInputExcel', 'openBaseResultsExcel', ...
    'openScenarioResultsExcel', 'openComparisonExcel'};
excelDescriptions = {'Entrada del caso cargado.', 'Entrada IEEE-118 sin la línea 26–30.', ...
    'Resultados guardados del caso base IEEE-118.', 'Resultados guardados sin la línea 26–30.', ...
    'Comparación guardada entre el caso base y el escenario.'};
excelButtons = cell(1, numel(excelLabels));
for excelIndex = 1:numel(excelLabels)
    excelButtons{excelIndex} = uibutton(excelGrid, 'Text', excelLabels{excelIndex}, ...
        'Tag', excelTags{excelIndex}, 'Enable', 'off', 'ButtonPushedFcn', @open_excel_file);
end
resetButton = uibutton(excelGrid, 'Text', 'Reset resultados', 'FontWeight', 'bold', ...
    'Tag', 'resetExcelResults', 'ButtonPushedFcn', @reset_excel_results, ...
    'Tooltip', sprintf(['Borra, previa confirmación, los seis Excel de salida conocidos de:\n%s\n', ...
        'Limpia las vistas de resultados sin cambiar entradas ni parámetros.'], outputFolder));

inputTabs = uitabgroup(mainGrid); inputTabs.Layout.Row = 7; inputTabs.Layout.Column = [1 4];
busTab = uitab(inputTabs, 'Title', 'Barras'); genTab = uitab(inputTabs, 'Title', 'Generadores'); branchTab = uitab(inputTabs, 'Title', 'Ramas');
busGrid = uigridlayout(busTab, [1 1]); genGrid = uigridlayout(genTab, [1 1]); branchGrid = uigridlayout(branchTab, [1 1]);
busTable = uitable(busGrid, 'Data', state.caseData.bus, 'ColumnEditable', true(1, width(state.caseData.bus)));
genTable = uitable(genGrid, 'Data', state.caseData.gen, 'ColumnEditable', true(1, width(state.caseData.gen)));
branchTable = uitable(branchGrid, 'Data', state.caseData.branch, 'ColumnEditable', true(1, width(state.caseData.branch)));
busTable.Tag = 'busInputs'; genTable.Tag = 'generatorInputs'; branchTable.Tag = 'branchInputs';

resultTabs = uitabgroup(mainGrid); resultTabs.Layout.Row = 8; resultTabs.Layout.Column = [1 4];
summaryTab = uitab(resultTabs, 'Title', 'Comparación'); summaryGrid = uigridlayout(summaryTab, [1 2]);
summaryTable = uitable(summaryGrid); convAxes = uiaxes(summaryGrid); convAxes.Title.String = 'Convergencia';
profileTab = uitab(resultTabs, 'Title', 'Perfil de tensión'); profileGrid = uigridlayout(profileTab, [1 2]); voltageAxes = uiaxes(profileGrid); angleAxes = uiaxes(profileGrid);
voltageAxes.Tag = 'voltageProfile'; angleAxes.Tag = 'angleProfile';
compareTab = uitab(resultTabs, 'Title', 'Base vs. salida 26–30');
compareGrid = uigridlayout(compareTab, [1 2]);
scenarioTable = uitable(compareGrid, 'Data', table(), 'Tag', 'scenarioComparison', ...
    'Tooltip', 'Diferencia = escenario menos base; NaN en identificadores, que no se restan.');
scenarioAxes = uiaxes(compareGrid, 'Tag', 'scenarioVoltage');
changesTab = uitab(resultTabs, 'Title', 'Cambios de flujo');
changesGrid = uigridlayout(changesTab, [1 2]);
globalPanel = uipanel(changesGrid, 'Title', 'Cinco mayores cambios (incluye retirada)');
activePanel = uipanel(changesGrid, 'Title', 'Redistribución: cinco ramas activas');
globalGrid = uigridlayout(globalPanel, [1 1]); activeGrid = uigridlayout(activePanel, [1 1]);
globalChanges = uitable(globalGrid, 'Data', table(), 'Tag', 'globalFlowChanges');
activeChanges = uitable(activeGrid, 'Data', table(), 'Tag', 'activeFlowChanges');
settingsControls = {methodDrop, tolField, maxField, relaxField, qCheck, fileField};
for settingIndex = 1:numel(settingsControls)
    settingsControls{settingIndex}.ValueChangedFcn = @invalidate_results;
end
inputTables = {busTable, genTable, branchTable};
for tableIndex = 1:numel(inputTables)
    inputTables{tableIndex}.CellEditCallback = @invalidate_results;
end
update_excel_buttons();

    function confirmed = confirm_excel_reset(message)
        choice = uiconfirm(fig, message, 'Reset de resultados Excel', ...
            'Options', {'Borrar resultados', 'Cancelar'}, 'DefaultOption', 2, ...
            'CancelOption', 2, 'Icon', 'warning', 'Interpreter', 'none');
        confirmed = strcmp(choice, 'Borrar resultados');
    end

    function reset_excel_results(~, ~)
        if state.busy, return; end
        set_busy(true);
        cleanup = onCleanup(@() set_busy(false)); %#ok<NASGU>
        try
            files = resultFiles(cellfun(@isfile, resultFiles));
            % Nunca se borra un libro que también se esté usando como entrada,
            % aunque tenga el nombre de una salida dentro de outputFolder.
            inputs = [caseFiles, {scenarioFile, state.inputFile, fileField.Value}];
            if ~isempty(state.base), inputs{end+1} = state.base.inputFile; end
            inputPaths = cellfun(@(p) char(java.io.File(p).getCanonicalPath()), ...
                inputs, 'UniformOutput', false);
            for fileIndex = 1:numel(files)
                path = char(java.io.File(files{fileIndex}).getCanonicalPath());
                assert(~any(strcmpi(path, inputPaths)), 'powerflow:ResetInputFile', ...
                    'No se puede borrar %s porque se está usando como entrada. Cargue otro caso antes de hacer reset.', ...
                    files{fileIndex});
            end
            listing = strjoin(files, newline);
            if isempty(files), listing = '(No hay Excel de salida guardados.)'; end
            message = sprintf(['Se eliminarán estos Excel de resultados:\n\n%s\n\n', ...
                'También se limpiarán las gráficas, tablas y resultados guardados en la interfaz.\n', ...
                'Las entradas y los parámetros actuales no cambian.\n', ...
                'Esta acción no se puede deshacer. Cierre los resultados en Excel antes de continuar.'], listing);
            if ~confirmReset(message), return; end
            failures = {};
            deletedCount = 0;
            for fileIndex = 1:numel(files)
                try
                    delete(files{fileIndex});
                    % delete puede emitir solo un warning cuando Excel bloquea
                    % el libro: se comprueba que realmente haya desaparecido.
                    assert(~isfile(files{fileIndex}), 'powerflow:ExcelNotDeleted', ...
                        'El archivo sigue en disco; puede estar abierto en Excel.');
                    deletedCount = deletedCount + 1;
                catch exception
                    failures{end+1} = sprintf('%s\n%s', files{fileIndex}, exception.message); %#ok<AGROW>
                end
            end
            clear_result_views();
            if isempty(failures)
                statusLabel.Text = 'Resultados reiniciados'; statusLabel.FontColor = [0.1 0.4 0.1];
                workflowLabel.Text = sprintf(['Reset completado: %d Excel eliminados. Entradas conservadas. ', ...
                    'Ejecute el caso cargado o seleccione IEEE-118 para empezar desde la base.'], deletedCount);
            else
                statusLabel.Text = 'Reset incompleto'; statusLabel.FontColor = [0.7 0.1 0.1];
                workflowLabel.Text = sprintf('%d Excel eliminados; %d pendientes. Cierre los archivos y vuelva a pulsar Reset resultados.', ...
                    deletedCount, numel(failures));
                uialert(fig, sprintf('No se pudieron borrar estos archivos:\n\n%s\n\nCierre Excel y vuelva a intentarlo.', ...
                    strjoin(failures, [newline newline])), 'Reset incompleto', 'Interpreter', 'none');
            end
            fprintf('GUI: %s\n', workflowLabel.Text);
        catch exception
            statusLabel.Text = 'Error en el reset'; statusLabel.FontColor = [0.7 0.1 0.1];
            fprintf(2, 'GUI: %s\n', exception.message);
            uialert(fig, exception.message, 'No se pudieron reiniciar los resultados', 'Interpreter', 'none');
        end
    end

    function open_excel_file(button, ~)
        if state.busy, return; end
        update_excel_buttons();
        filename = button.UserData;
        try
            assert(isfile(filename), 'powerflow:MissingExcelFile', ...
                'El archivo no existe. Cargue la entrada o ejecute el estudio para generar los resultados.');
            openExcel(filename);
        catch exception
            fprintf(2, 'GUI: no se pudo abrir %s: %s\n', filename, exception.message);
            uialert(fig, sprintf(['Archivo: %s\n\n%s\n\n', ...
                'Compruebe que Excel u otra aplicación esté asociada a los archivos .xlsx.'], ...
                filename, exception.message), 'No se pudo abrir Excel', 'Interpreter', 'none');
        end
    end

    function update_excel_buttons()
        paths = {state.inputFile, scenarioFile, baseOutput, scenarioOutput, comparisonOutput};
        for buttonIndex = 1:numel(excelButtons)
            button = excelButtons{buttonIndex};
            button.UserData = paths{buttonIndex};
            button.Tooltip = sprintf('%s\n%s\nAbre el archivo guardado; no guarda cambios de la interfaz.', ...
                excelDescriptions{buttonIndex}, paths{buttonIndex});
            button.Enable = 'off';
            if isfile(paths{buttonIndex})
                if ~state.busy, button.Enable = 'on'; end
            else
                button.Tooltip = sprintf('%s\nPendiente: cargue la entrada o genere los resultados.', button.Tooltip);
            end
        end
    end

    function select_case(~, ~)
        index = find(strcmp(caseLabels, caseDrop.Value), 1);
        if isempty(index)
            caseDrop.Value = state.caseSelection;
            select_file([], []);
            return;
        end
        fileField.Value = caseFiles{index};
        if load_file([], [])
            run_case([], []);
        else
            fileField.Value = state.inputFile;
        end
    end

    function select_file(~, ~)
        [file, path] = uigetfile({'*.xlsx;*.xls', 'Archivos Excel'}, 'Seleccionar caso');
        if isequal(file, 0), return; end
        fileField.Value = fullfile(path, file);
        load_file([], []);
    end

    function loaded = load_file(~, ~)
        loaded = false;
        try
            caseData = load_case_excel(fileField.Value);
            [~, fileInfo] = fileattrib(fileField.Value);
            index = find(strcmpi(fileInfo.Name, caseFiles), 1);
            state.caseSelection = 'Personalizado';
            if ~isempty(index), state.caseSelection = caseLabels{index}; end
            state.caseData = caseData;
            state.inputFile = fileInfo.Name;
            fileField.Value = state.inputFile;
            removeStyle(branchTable);
            caseDrop.Value = state.caseSelection;
            busTable.Data = state.caseData.bus; genTable.Data = state.caseData.gen; branchTable.Data = state.caseData.branch;
            [recommendedIterations, iterationsAdjusted] = recommended_max_iterations(state.caseData, maxField.Value);
            if iterationsAdjusted, maxField.Value = recommendedIterations; end
            clear_result_views();
            statusLabel.Text = sprintf('Cargado: %d barras, %d ramas', state.caseData.nBus, state.caseData.nBranch);
            if iterationsAdjusted
                statusLabel.Text = sprintf('%s | iteraciones ajustadas a %d', statusLabel.Text, maxField.Value);
            end
            statusLabel.FontColor = [0.1 0.4 0.1];
            loaded = true;
        catch exception
            caseDrop.Value = state.caseSelection;
            fileField.Value = state.inputFile;
            update_workflow_controls();
            fprintf(2, 'GUI: %s\n', exception.message);
            uialert(fig, exception.message, 'Error al cargar Excel');
        end
    end

    function clear_result_views()
        state.results = []; state.base = []; state.analysis = []; state.phase = 'case';
        summaryTable.Data = table(); scenarioTable.Data = table();
        globalChanges.Data = table(); activeChanges.Data = table();
        for ax = [convAxes, voltageAxes, angleAxes, scenarioAxes]
            cla(ax);
            legend(ax, 'off');
        end
        update_workflow_controls();
    end

    function invalidate_results(~, ~)
        clear_result_views();
        statusLabel.Text = 'Datos/parámetros cambiados';
        workflowLabel.Text = 'Resultados invalidados. Cargue y ejecute nuevamente el caso base antes de retirar la línea.';
    end

    function run_case(~, ~)
        if state.busy, return; end
        set_busy(true);
        cleanup = onCleanup(@() set_busy(false));
        clear_result_views();
        try
            assert_loaded_file();
            statusLabel.Text = 'Calculando...';
            drawnow limitrate nocallbacks;
            state.caseData = current_case();
            validate_case(state.caseData);
            options = current_options();
            if strcmp(methodDrop.Value, 'Todos')
                selected = {'Newton-Raphson','Gauss-Seidel','Desacoplado rápido'};
            else
                selected = {methodDrop.Value};
            end
            state.results = calculate_methods(state.caseData, selected, options);
            update_result_views();
            statusLabel.Text = 'Cálculo terminado'; statusLabel.FontColor = [0.1 0.4 0.1];
            if ~all([state.results.converged])
                statusLabel.Text = 'Hay métodos sin converger'; statusLabel.FontColor = [0.7 0.1 0.1];
            end
            if state.caseData.nBus == 118 && all(state.caseData.branch.STATUS ~= 0) && ...
                    same_case(state.caseData, referenceCase) && numel(state.results) == 3 && ...
                    all([state.results.converged]) && all([state.results.maxMismatch] <= 1e-8) && ...
                    options.tolerance <= 1e-8 && ~options.enforceQLimits
                export_results_excel(baseOutput, state.caseData, state.results);
                state.base = struct('caseData', state.caseData, 'results', state.results, ...
                    'options', options, 'inputFile', state.inputFile, 'caseSelection', state.caseSelection);
                state.phase = 'base';
                workflowLabel.Text = 'Caso base exportado. Ahora puede pulsar «Retirar línea 26–30».';
                fprintf('GUI: caso base con todas las ramas activas exportado a %s\n', baseOutput);
            else
                workflowLabel.Text = 'Para habilitar la salida: IEEE-118 original, Todos convergentes, tolerancia <=1e-8 y límites Q desactivados.';
            end
        catch exception
            statusLabel.Text = 'Error en el cálculo';
            statusLabel.FontColor = [0.7 0.1 0.1];
            workflowLabel.Text = 'No hay un caso base válido para retirar la línea. Revise los datos y vuelva a ejecutar.';
            fprintf(2, 'GUI: %s\n', exception.message);
            uialert(fig, exception.message, 'Error durante la solución');
        end
    end

    function run_outage(~, ~)
        if state.busy, return; end
        % También se comprueba al pulsar: evita usar resultados obsoletos si se
        % cambiaron controles o tablas por código sin disparar sus callbacks.
        if ~base_is_current()
            clear_result_views();
            workflowLabel.Text = 'Primero ejecute el caso base IEEE-118 con Todos y sin editar sus datos.';
            return;
        end
        set_busy(true);
        cleanup = onCleanup(@() set_busy(false));
        try
            assert_loaded_file();
            assert(isfile(scenarioFile), 'powerflow:MissingScenario', ...
                'Falta la copia resaltada. Ejecute: python tools/prepare_scenario1.py');
            scenarioCase = load_case_excel(scenarioFile);
            removed = validate_line_outage(state.base.caseData, scenarioCase);
            statusLabel.Text = 'Retirando línea...';
            workflowLabel.Text = 'Calculando escenario con los mismos parámetros del caso base...';
            drawnow limitrate nocallbacks;
            selected = {'Newton-Raphson','Gauss-Seidel','Desacoplado rápido'};
            results = calculate_methods(scenarioCase, selected, state.base.options);
            analysis = compare_scenario1(state.base.caseData, scenarioCase, state.base.results, results);
            % Se exporta exactamente el snapshot base, nunca una nueva corrida.
            export_results_excel(baseOutput, state.base.caseData, state.base.results);
            export_results_excel(scenarioOutput, scenarioCase, results);
            compare_scenario1(state.base.caseData, scenarioCase, state.base.results, results, comparisonOutput);
            state.caseData = scenarioCase; state.results = results;
            state.inputFile = scenarioFile; state.caseSelection = 'Personalizado';
            state.analysis = analysis; state.phase = 'scenario';
            fileField.Value = scenarioFile; caseDrop.Value = state.caseSelection;
            show_input_tables();
            inputTabs.SelectedTab = branchTab;
            drawnow nocallbacks;
            scroll(branchTable, 'row', removed);
            column = find(strcmp(branchTable.Data.Properties.VariableNames, 'STATUS'));
            addStyle(branchTable, uistyle('BackgroundColor', [1 .94 .65], ...
                'FontColor', [0 0 0]), 'row', removed);
            addStyle(branchTable, uistyle('BackgroundColor', [1 .75 .25], ...
                'FontColor', [0 0 0], 'FontWeight', 'bold'), 'cell', [removed column]);
            update_result_views(); update_scenario_views();
            resultTabs.SelectedTab = compareTab;
            statusLabel.Text = 'Escenario exportado'; statusLabel.FontColor = [0.1 0.4 0.1];
            workflowLabel.Text = 'Línea 26–30 fuera de servicio. Base conservada; comparación y ambos Excel exportados.';
            fprintf('GUI: escenario exportado a %s\nComparación exportada a %s\n', scenarioOutput, comparisonOutput);
        catch exception
            statusLabel.Text = 'Error en el escenario'; statusLabel.FontColor = [0.7 0.1 0.1];
            workflowLabel.Text = 'No se completó la salida/comparación. El caso base se conserva; revise el error antes de reintentar.';
            fprintf(2, 'GUI: %s\n', exception.message);
            uialert(fig, exception.message, 'Error al retirar línea 26–30');
        end
    end

    function restore_base(~, ~)
        if state.busy || isempty(state.base), return; end
        state.caseData = state.base.caseData; state.results = state.base.results;
        state.inputFile = state.base.inputFile; state.caseSelection = state.base.caseSelection;
        state.phase = 'base';
        fileField.Value = state.inputFile; caseDrop.Value = state.caseSelection;
        tolField.Value = state.base.options.tolerance;
        maxField.Value = state.base.options.maxIterations;
        relaxField.Value = state.base.options.relaxation;
        qCheck.Value = state.base.options.enforceQLimits; methodDrop.Value = 'Todos';
        show_input_tables(); update_result_views(); update_workflow_controls();
        statusLabel.Text = 'Caso base restaurado';
        workflowLabel.Text = 'Línea 26–30 activa otra vez. Se muestran los resultados base guardados, sin recalcular.';
    end

    function caseData = current_case()
        caseData = state.caseData;
        caseData.bus = gui_table(busTable.Data, caseData.bus.Properties.VariableNames);
        caseData.gen = gui_table(genTable.Data, caseData.gen.Properties.VariableNames);
        caseData.branch = gui_table(branchTable.Data, caseData.branch.Properties.VariableNames);
        caseData.nBus = height(caseData.bus); caseData.nBranch = height(caseData.branch);
        caseData.nGen = height(caseData.gen);
    end

    function options = current_options()
        options = struct('tolerance', tolField.Value, 'maxIterations', maxField.Value, ...
            'relaxation', relaxField.Value, 'enforceQLimits', qCheck.Value, 'verbose', true);
    end

    function results = calculate_methods(caseData, selected, options)
        cells = cell(1, numel(selected));
        for ii = 1:numel(selected)
            fprintf('\nGUI | %s | %s\n', char(caseData.name), selected{ii});
            cells{ii} = solve_power_flow(caseData, selected{ii}, options);
        end
        results = [cells{:}];
    end

    function equal = same_case(a, b)
        equal = a.baseMVA == b.baseMVA && isequaln(a.bus, b.bus) && ...
            isequaln(a.gen, b.gen) && isequaln(a.branch, b.branch);
    end

    function valid = base_is_current()
        valid = false;
        if isempty(state.base) || ~strcmp(state.phase, 'base'), return; end
        try
            valid = strcmp(methodDrop.Value, 'Todos') && ...
                isequal(current_options(), state.base.options) && ...
                same_case(current_case(), state.base.caseData) && ...
                strcmpi(fileField.Value, state.base.inputFile);
        catch
            valid = false;
        end
    end

    function assert_loaded_file()
        [ok, info] = fileattrib(fileField.Value);
        assert(ok && strcmpi(info.Name, state.inputFile), 'powerflow:UnloadedGUIFile', ...
            'La ruta cambió: pulse «Cargar caso» antes de ejecutar.');
    end

    function show_input_tables()
        busTable.Data = state.caseData.bus; genTable.Data = state.caseData.gen;
        branchTable.Data = state.caseData.branch;
        removeStyle(branchTable);
    end

    function set_busy(busy)
        if ~isvalid(fig), return; end
        state.busy = busy;
        enabled = 'on'; if busy, enabled = 'off'; end
        busyControls = {caseDrop, fileField, selectButton, loadButton, methodDrop, ...
            tolField, maxField, relaxField, qCheck, runButton, resetButton};
        for busyIndex = 1:numel(busyControls)
            busyControls{busyIndex}.Enable = enabled;
        end
        % Impide editar sin desmontar tablas de pestañas ocultas (Enable off/on
        % puede dejar su render vacío en algunas versiones de uifigure).
        editingTables = {busTable, genTable, branchTable};
        for editIndex = 1:numel(editingTables)
            editingTables{editIndex}.ColumnEditable = ~busy;
        end
        update_workflow_controls();
    end

    function update_workflow_controls()
        update_excel_buttons();
        outageButton.Enable = 'off'; restoreButton.Enable = 'off';
        if state.busy, return; end
        if base_is_current(), outageButton.Enable = 'on'; end
        if ~isempty(state.base) && strcmp(state.phase, 'scenario'), restoreButton.Enable = 'on'; end
    end

    function update_scenario_views()
        scenarioTable.Data = state.analysis.comparacion;
        scenarioTable.ColumnName = {'Variable','Caso base','Escenario','Diferencia'};
        scenarioTable.ColumnWidth = {260,100,100,100};
        columns = {'Desde','Hasta','S_base_MVA','S_escenario_MVA','Delta_MVA','Delta_pct'};
        globalChanges.Data = state.analysis.cambios_top5_total(:,columns);
        activeChanges.Data = state.analysis.cambios_top5(:,columns);
        globalChanges.ColumnName = {'Desde','Hasta','Base (MVA)','Escenario (MVA)','Cambio (MVA)','Cambio (%)'};
        activeChanges.ColumnName = globalChanges.ColumnName;
        cla(scenarioAxes); hold(scenarioAxes, 'on'); grid(scenarioAxes, 'on');
        b = state.base.results(1).busResults; s = state.results(1).busResults;
        plot(scenarioAxes, b.BUS_I, b.VM_pu, 'LineWidth', 1.4, 'DisplayName', 'Caso base');
        plot(scenarioAxes, s.BUS_I, s.VM_pu, '--', 'LineWidth', 1.4, 'DisplayName', 'Sin línea 26–30');
        yline(scenarioAxes, .95, ':r', 'HandleVisibility', 'off');
        yline(scenarioAxes, 1.05, ':r', 'HandleVisibility', 'off');
        scenarioAxes.Title.String = 'Caso base vs. salida de línea (NR)';
        scenarioAxes.XLabel.String = 'Barra'; scenarioAxes.YLabel.String = '|V| (pu)';
        legend(scenarioAxes, 'show');
    end

    function T = gui_table(data, variableNames)
        if istable(data)
            T = data;
        else
            T = cell2table(data, 'VariableNames', variableNames);
        end
        T.Properties.VariableNames = variableNames;
    end

    function update_result_views()
        comparison = result_comparison(state.results);
        comparison = renamevars(comparison, {'Error_final_pu','Perdidas_P_MW'}, {'ErrorFinalPU','PerdidasPMW'});
        summaryTable.Data = comparison;
        summaryTable.ColumnName = {'Método','Convergió','Iteraciones','Error final (pu)','Tiempo (s)', ...
            'Pérdidas P (MW)','Q neta ramas (MVAr)','P Slack (MW)','Q Slack (MVAr)'};
        plot_convergence(convAxes, state.results);
        cla(voltageAxes); hold(voltageAxes, 'on'); grid(voltageAxes, 'on');
        cla(angleAxes); hold(angleAxes, 'on'); grid(angleAxes, 'on');
        for ii = 1:numel(state.results)
            plot(voltageAxes, state.results(ii).busResults.BUS_I, state.results(ii).busResults.VM_pu, 'DisplayName', state.results(ii).method);
            plot(angleAxes, state.results(ii).busResults.BUS_I, state.results(ii).busResults.VA_deg, 'DisplayName', state.results(ii).method);
        end
        voltageAxes.YLabel.String = '|V| (pu)'; voltageAxes.XLabel.String = 'Barra'; voltageAxes.Title.String = 'Perfil de tensión'; legend(voltageAxes, 'show');
        angleAxes.YLabel.String = 'Ángulo (°)'; angleAxes.XLabel.String = 'Barra'; angleAxes.Title.String = 'Ángulo'; legend(angleAxes, 'show');
    end

end
