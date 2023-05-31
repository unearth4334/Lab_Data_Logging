function result = loadData(filename)
    % Load the tab-delimited data file
    data = readtable(filename, 'Delimiter', '\t');

    % Initialize variables to store extracted values and standard deviations
    values = struct();
    stdDevs = struct();
    minValues = struct();
    maxValues = struct();

    skip = false;

    % Iterate over the table columns
    for i = 1:size(data, 2)

        if skip
            skip = false;
            continue;
        end

        % Extract the column name
        colName = data.Properties.VariableNames{i};
        result.(colName) = struct();

        % Check if the column has the format "Name" and "Name_e"
        if i < size(data, 2) && strcmp(colName, data.Properties.VariableNames{i+1}(1:end-2))
            % Extract values and standard deviations
            values.(colName) = data.(colName);
            stdDevs.(colName) = data.(data.Properties.VariableNames{i+1});
            
            % Skip the next column
            skip = true;

        elseif isnumeric(data.(colName))
            values.(colName) = data.(colName);

        % Check if the column values have the format "[A, B]"
        elseif count(data.(colName), ',') == 1
            % Extract values and standard deviations
            parsedData = cellfun(@(x) sscanf(x, '[%f, %f]'), data.(colName), 'UniformOutput', false);
            
            % Store the extracted values and standard deviations
            for j = 1:length(parsedData)
                values.(colName)(j) = parsedData{j}(1);
                stdDevs.(colName)(j) = parsedData{j}(2);
            end

        % Check if the column values have the format "[A, B, C, D]"
        elseif count(data.(colName), ',') == 3
            % Extract values, standard deviations, minimum values, and maximum values
            parsedData = cellfun(@(x) sscanf(x, '[%f, %f, %f, %f]'), data.(colName), 'UniformOutput', false);

            % Store the extracted values, standard deviations, minimum values, and maximum values
            for j = 1:length(parsedData)
                values.(colName)(j) = parsedData{j}(1);
                stdDevs.(colName)(j) = parsedData{j}(2);
                minValues.(colName)(j) = parsedData{j}(3);
                maxValues.(colName)(j) = parsedData{j}(4);
            end
        end

        try
            result.(colName).value = reshape(values.(colName), 1, []);
            result.(colName).std = reshape(stdDevs.(colName), 1, []);
            result.(colName).min = reshape(minValues.(colName), 1, []);
            result.(colName).max = reshape(maxValues.(colName), 1, []);
        catch
            % do nothing %
        end
    end
    
    % Display a message indicating successful extraction
    disp('Data extraction completed.');
end