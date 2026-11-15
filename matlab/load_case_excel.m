function caseData = load_case_excel(filename)
%LOAD_CASE_EXCEL Lee un caso de flujo de potencia desde Excel.
%   El libro debe contener las hojas bus, gen y branch. La hoja config
%   puede contener la baseMVA; si no existe, se usa 100 MVA.

if nargin < 1 || strlength(string(filename)) == 0
    error('Debe indicar un archivo Excel.');
end
filename = char(filename);
if ~isfile(filename)
    error('No existe el archivo: %s', filename);
end

sheets = sheetnames(filename);
busSheet = find_sheet(sheets, ["bus", "barras"]);
genSheet = find_sheet(sheets, ["gen", "generadores", "generator"]);
branchSheet = find_sheet(sheets, ["branch", "ramas", "lineas", "line"]);
configSheet = find_sheet(sheets, ["config", "basemva"], false);

bus = canonical_table(readtable(filename, 'Sheet', busSheet, 'VariableNamingRule', 'preserve'));
gen = canonical_table(readtable(filename, 'Sheet', genSheet, 'VariableNamingRule', 'preserve'));
branch = canonical_table(readtable(filename, 'Sheet', branchSheet, 'VariableNamingRule', 'preserve'));

if isempty(configSheet)
    baseMVA = 100;
else
    config = readtable(filename, 'Sheet', configSheet, 'VariableNamingRule', 'preserve');
    values = table2array(config);
    if iscell(values)
        values = str2double(string(values));
    end
    values = double(values(:));
    values = values(isfinite(values));
    baseMVA = values(1);
end

required.bus = {'BUS_I', 'TYPE', 'PD', 'QD'};
required.gen = {'GEN_BUS', 'PG', 'QG'};
required.branch = {'F_BUS', 'T_BUS', 'BR_R', 'BR_X'};
check_required(bus, required.bus, 'bus');
check_required(gen, required.gen, 'gen');
check_required(branch, required.branch, 'branch');

bus = add_default(bus, 'GS', 0); bus = add_default(bus, 'BS', 0);
bus = add_default(bus, 'AREA', 1); bus = add_default(bus, 'VM', 1); bus = add_default(bus, 'VA', 0);
bus = add_default(bus, 'BASE_KV', 0); bus = add_default(bus, 'ZONE', 1);
bus = add_default(bus, 'VMAX', 1.10); bus = add_default(bus, 'VMIN', 0.90);

vgOmitted = ~ismember('VG', gen.Properties.VariableNames);
gen = add_default(gen, 'QMAX', inf); gen = add_default(gen, 'QMIN', -inf);
gen = add_default(gen, 'VG', NaN); gen = add_default(gen, 'MBASE', baseMVA);
gen = add_default(gen, 'STATUS', 1); gen = add_default(gen, 'PMAX', inf); gen = add_default(gen, 'PMIN', -inf);

branch = add_default(branch, 'BR_B', 0); branch = add_default(branch, 'RATE_A', 0);
branch = add_default(branch, 'RATE_B', 0); branch = add_default(branch, 'RATE_C', 0);
branch = add_default(branch, 'TAP', 1); branch = add_default(branch, 'SHIFT', 0);
branch = add_default(branch, 'STATUS', 1); branch = add_default(branch, 'ANGMIN', -360); branch = add_default(branch, 'ANGMAX', 360);

bus = numeric_table(bus, {'BUS_I','TYPE','PD','QD','GS','BS','AREA','VM','VA','BASE_KV','ZONE','VMAX','VMIN'});
gen = numeric_table(gen, {'GEN_BUS','PG','QG','QMAX','QMIN','VG','MBASE','STATUS','PMAX','PMIN'});
branch = numeric_table(branch, {'F_BUS','T_BUS','BR_R','BR_X','BR_B','RATE_A','RATE_B','RATE_C','TAP','SHIFT','STATUS','ANGMIN','ANGMAX'});

bus = sortrows(bus, 'BUS_I');
if vgOmitted
    [found, busRows] = ismember(gen.GEN_BUS, bus.BUS_I);
    gen.VG(found) = bus.VM(busRows(found));
end
[~, caseName] = fileparts(filename);
caseData = struct('baseMVA', baseMVA, 'bus', bus, 'gen', gen, 'branch', branch, ...
    'name', string(caseName));
caseData.nBus = height(bus);
caseData.nBranch = height(branch);
caseData.nGen = height(gen);
validate_case(caseData);
end

function sheet = find_sheet(sheets, candidates, required)
if nargin < 3, required = true; end
keys = normalize_key(sheets);
sheet = '';
for c = candidates
    hit = find(keys == normalize_key(c), 1);
    if ~isempty(hit)
        sheet = sheets(hit);
        return;
    end
end
if required
    error('No se encontró una hoja equivalente a: %s', strjoin(candidates, ', '));
end
end

function T = canonical_table(T)
raw = string(T.Properties.VariableNames);
canonical = raw;
for k = 1:numel(raw)
    key = normalize_key(raw(k));
    canonical(k) = alias_for(key);
end
for k = 1:numel(raw)
    if canonical(k) ~= raw(k) && ~ismember(canonical(k), T.Properties.VariableNames)
        T = renamevars(T, raw(k), canonical(k));
    end
end
end

function canonical = alias_for(key)
canonical = key;
aliases = {
    'BUS_I', {'BUS_I','BUS','BUS_ID','BARRA','NUM_BARRA','NUMBUS'};
    'TYPE', {'TYPE','TIPO','TIPO_BARRA','BUSTYPE'};
    'PD', {'PD','PLOAD','P_CARGA','PCARGA','DEMANDA_P','PDEMANDA'};
    'QD', {'QD','QLOAD','Q_CARGA','QCARGA','DEMANDA_Q','QDEMANDA'};
    'GS', {'GS','G_SHUNT'}; 'BS', {'BS','B_SHUNT'}; 'AREA', {'AREA'};
    'VM', {'VM','V_MAG','VOLTAGE','MAG_V'}; 'VA', {'VA','V_ANG','ANGLE','ANGULO'};
    'BASE_KV', {'BASE_KV','BASEKV','KV_BASE'}; 'ZONE', {'ZONE','ZONA'};
    'VMAX', {'VMAX','V_MAX'}; 'VMIN', {'VMIN','V_MIN'};
    'GEN_BUS', {'GEN_BUS','GENBUS','BARRA_GEN','BARRA_GENERADOR'};
    'PG', {'PG','P_GEN','PGENERADA','GENERACION_P'}; 'QG', {'QG','Q_GEN','QGENERADA','GENERACION_Q'};
    'QMAX', {'QMAX','Q_MAX'}; 'QMIN', {'QMIN','Q_MIN'}; 'VG', {'VG','V_GEN'};
    'MBASE', {'MBASE','MVA_BASE'}; 'STATUS', {'STATUS','ESTADO','IN_SERVICE'};
    'PMAX', {'PMAX','P_MAX'}; 'PMIN', {'PMIN','P_MIN'};
    'F_BUS', {'F_BUS','FROM','FROM_BUS','BARRA_INICIO','DESDE'};
    'T_BUS', {'T_BUS','TO','TO_BUS','BARRA_FIN','HASTA'};
    'BR_R', {'BR_R','R','RESISTENCIA'}; 'BR_X', {'BR_X','X','REACTANCIA'};
    'BR_B', {'BR_B','B','SUSCEPTANCIA'}; 'RATE_A', {'RATE_A','RATEA','LIMITE_MVA'};
    'RATE_B', {'RATE_B','RATEB'}; 'RATE_C', {'RATE_C','RATEC'};
    'TAP', {'TAP','RELACION_TAP'}; 'SHIFT', {'SHIFT','DESFASE'};
    'ANGMIN', {'ANGMIN','ANG_MIN'}; 'ANGMAX', {'ANGMAX','ANG_MAX'};
    };
for r = 1:size(aliases,1)
    candidates = string(aliases{r,2});
    if any(key == normalize_key(candidates))
        canonical = string(aliases{r,1});
        return;
    end
end
end

function key = normalize_key(value)
key = upper(string(value));
key = replace(key, ["Á","À","Ä","Â"], "A");
key = replace(key, ["É","È","Ë","Ê"], "E");
key = replace(key, ["Í","Ì","Ï","Î"], "I");
key = replace(key, ["Ó","Ò","Ö","Ô"], "O");
key = replace(key, ["Ú","Ù","Ü","Û"], "U");
key = replace(key, "Ñ", "N");
key = regexprep(key, '[^A-Z0-9]', '');
end

function check_required(T, required, label)
missing = required(~ismember(required, T.Properties.VariableNames));
if ~isempty(missing)
    error('Faltan columnas en la hoja %s: %s', label, strjoin(missing, ', '));
end
end

function T = add_default(T, name, value)
if ~ismember(name, T.Properties.VariableNames)
    T.(name) = repmat(value, height(T), 1);
end
end

function T = numeric_table(T, names)
for name = names
    value = T.(name{1});
    if iscell(value) || isstring(value)
        value = str2double(string(value));
    end
    T.(name{1}) = double(value);
end
end
