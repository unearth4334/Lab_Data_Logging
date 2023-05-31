function plotData(x, y, varargin)
    if isempty(varargin)
        varargin = '-';
    end
    if isfield(x, 'std') && isfield(y, 'std')
        % Plot with error bars
        errorbar(x.value, y.value, y.std, y.std, x.std, x.std, varargin);
    elseif isfield(x, 'std')
        % Plot with error bars
        errorbar(x.value, y.value, x.std,'horizontal', varargin);
    elseif isfield(y, 'std')
        % Plot with error bars
        errorbar(x.value, y.value, y.std, varargin);
    else
        % Plot without error bars
        plot(x.value, y.value, varargin);
    end
end