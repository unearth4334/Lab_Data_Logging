% Plot EL34143A sweep data comparing load and API measurements
% 
% This script reads CSV data from the EL34143A sweep test and creates:
% - Main plot: Load current vs API current
% - Bottom plot: Error (difference) between measurements
%
% Usage:
%   plot_el34143a_sweep('el34143a_sweep_20260218_165551.csv')
%   plot_el34143a_sweep()  % Opens file dialog

function plot_el34143a_sweep(filename)
    % If no filename provided, open file dialog
    if nargin < 1
        [file, path] = uigetfile('*.csv', 'Select EL34143A sweep data file');
        if isequal(file, 0)
            disp('User canceled file selection');
            return;
        end
        filename = fullfile(path, file);
    end
    
    % Check if file exists
    if ~exist(filename, 'file')
        error('File not found: %s', filename);
    end
    
    % Read CSV data
    fprintf('Reading data from: %s\n', filename);
    data = readtable(filename);
    
    % Extract columns
    setpoint = data.setpoint_current;
    voltage = data.voltage;
    measured_current = data.measured_current;
    power = data.power;
    avdd_current = data.avdd_current;
    difference = data.difference;
    difference_percent = data.difference_percent;
    
    % Check if API data is available
    has_api_data = ~all(isnan(avdd_current));
    
    if ~has_api_data
        warning('No API data found in CSV. API columns are empty.');
        fprintf('Only load measurements will be plotted.\n');
    end
    
    % Set consistent font size
    font_size = 12;
    title_font_size = 14;
    
    % Create figure
    figure('Position', [100, 100, 1200, 800], 'Color', 'white');
    
    % Determine subplot heights (main plot 75%, error plot 25%)
    if has_api_data
        % Main plot - Current comparison
        subplot('Position', [0.08, 0.35, 0.88, 0.58]);
        
        plot(setpoint * 1000, measured_current * 1000, 'b-o', ...
             'LineWidth', 2, 'MarkerSize', 6, 'DisplayName', 'Load Measured');
        hold on;
        plot(setpoint * 1000, avdd_current * 1000, 'r-s', ...
             'LineWidth', 2, 'MarkerSize', 6, 'DisplayName', 'API (GUI)');
        plot(setpoint * 1000, setpoint * 1000, 'k--', ...
             'LineWidth', 1, 'DisplayName', 'Setpoint');
        hold off;
        
        grid on;
        ylabel('Current (mA)', 'FontSize', font_size, 'FontWeight', 'bold');
        title('EL34143A Load Current vs API Current Comparison', ...
              'FontSize', title_font_size, 'FontWeight', 'bold');
        legend('Location', 'northwest', 'FontSize', font_size);
        set(gca, 'FontSize', font_size);
        
        % Remove x-axis label from top plot
        set(gca, 'XTickLabel', []);
        
        % Bottom plot - Error
        subplot('Position', [0.08, 0.08, 0.88, 0.18]);
        
        % Plot absolute error
        plot(setpoint * 1000, difference * 1000, 'mo-', ...
             'LineWidth', 2, 'MarkerSize', 6);
        hold on;
        % Add zero reference line
        plot([min(setpoint) max(setpoint)] * 1000, [0 0], 'k--', 'LineWidth', 1);
        hold off;
        
        grid on;
        xlabel('Setpoint Current (mA)', 'FontSize', font_size, 'FontWeight', 'bold');
        ylabel('Error (mA)', 'FontSize', font_size, 'FontWeight', 'bold');
        title('Measurement Error (Load - API)', 'FontSize', font_size, 'FontWeight', 'bold');
        set(gca, 'FontSize', font_size);
        
        % Calculate and display statistics
        mean_error = mean(difference, 'omitnan') * 1000;
        std_error = std(difference, 'omitnan') * 1000;
        max_error = max(abs(difference), [], 'omitnan') * 1000;
        mean_percent = mean(abs(difference_percent), 'omitnan');
        
        % Add text annotation with statistics
        text_str = sprintf('Mean Error: %.3f mA\nStd Dev: %.3f mA\nMax Error: %.3f mA\nMean %%Error: %.2f%%', ...
                          mean_error, std_error, max_error, mean_percent);
        annotation('textbox', [0.72, 0.10, 0.25, 0.12], 'String', text_str, ...
                  'FontSize', font_size-1, 'BackgroundColor', 'white', ...
                  'EdgeColor', 'black', 'LineWidth', 1);
        
    else
        % Only load data available - single plot
        subplot('Position', [0.08, 0.15, 0.88, 0.78]);
        
        plot(setpoint * 1000, measured_current * 1000, 'b-o', ...
             'LineWidth', 2, 'MarkerSize', 6, 'DisplayName', 'Load Measured');
        hold on;
        plot(setpoint * 1000, setpoint * 1000, 'k--', ...
             'LineWidth', 1, 'DisplayName', 'Setpoint');
        hold off;
        
        grid on;
        xlabel('Setpoint Current (mA)', 'FontSize', font_size, 'FontWeight', 'bold');
        ylabel('Measured Current (mA)', 'FontSize', font_size, 'FontWeight', 'bold');
        title('EL34143A Load Current vs Setpoint', ...
              'FontSize', title_font_size, 'FontWeight', 'bold');
        legend('Location', 'northwest', 'FontSize', font_size);
        set(gca, 'FontSize', font_size);
        
        % Display warning
        annotation('textbox', [0.35, 0.45, 0.3, 0.1], ...
                  'String', 'API data not available in this sweep', ...
                  'FontSize', font_size, 'Color', 'red', ...
                  'HorizontalAlignment', 'center', ...
                  'BackgroundColor', 'yellow', 'EdgeColor', 'red', 'LineWidth', 2);
    end
    
    % Add overall figure title with filename
    [~, name, ext] = fileparts(filename);
    sgtitle(sprintf('Data File: %s%s', name, ext), 'FontSize', font_size, 'FontWeight', 'normal');
    
    % Print summary to console
    fprintf('\n--- Sweep Summary ---\n');
    fprintf('Total points: %d\n', length(setpoint));
    fprintf('Current range: %.3f to %.3f A\n', min(setpoint), max(setpoint));
    fprintf('Voltage range: %.3f to %.3f V\n', min(voltage), max(voltage));
    fprintf('Power range: %.3f to %.3f W\n', min(power), max(power));
    
    if has_api_data
        fprintf('\n--- Error Statistics ---\n');
        fprintf('Mean error: %.4f mA (%.3f%%)\n', mean_error, mean_percent);
        fprintf('Std deviation: %.4f mA\n', std_error);
        fprintf('Max error: %.4f mA\n', max_error);
        fprintf('RMS error: %.4f mA\n', rms(difference, 'omitnan') * 1000);
    end
    
    fprintf('\nPlot complete!\n');
end
