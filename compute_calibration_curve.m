clear
clc

% Open a file selection dialog for a CSV file
[filename, pathname] = uigetfile({'*.csv', 'CSV Files (*.csv)'}, ...
                                 'Select a CSV file');

% If the user cancels, exit gracefully
if isequal(filename,0)
    disp('No file selected.');
    return;
end

% Construct the full file path
filepath = fullfile(pathname, filename);

% Read the CSV into a table named df
df = readtable(filepath);

% Display a message confirming the load
disp('CSV file successfully loaded into table variable "df".');


%% Ensure timestamps are in milliseconds and flow in mL/min
t = df.timestamp_ms;          % ms
flow = df.flow_rate_ml_min;   % mL/min

% Convert flow to mL/ms
flow_mL_per_ms = flow / (60 * 1000);

% Create time differences (ms)
dt = [0; diff(t)];

% Incremental volume (mL)
dV_mL = flow_mL_per_ms .* dt;

% Cumulative volume (µL)
df.vol_ul = cumsum(dV_mL) * 1000;   % convert mL to µL

%%
close all
ax = draw.jaxes;
ax.Position = [0.2,0.2,0.6,0.6]
yyaxis left
plot(df.timestamp_ms/1000,df.flow_rate_ml_min,'LineWidth',1);
ylim([-20,35])
ylabel('Flow Rate (mL/min)')
yyaxis right
plot(df.timestamp_ms/1000,df.vol_ul,'LineWidth',2);

ylabel('Cumulative Volume (uL)')
xlabel('Time (s)')
xlim([0,350])
title("Sampling 20ms:20ms:180ms on-time, 50 Reps each")

%%
Duration = (0.02:0.02:0.18)';
% t_trials = 1000*[0,39.947,78.203,116.267,153.703,192.329,230.422,268.518,306.084,348.436];

idx = find(df.flow_rate_ml_min < 0.1);
split_idx = [1; find(diff(idx) > 1) + 1];
seg_start = idx(split_idx);
seg_len = diff([split_idx; numel(idx)+1]);
valid = seg_len >= 500;
timepoints = df.timestamp_ms(seg_start(valid));
timepoints = timepoints(1:min(10,end));

t_trials = timepoints;
Cumulative_Vol = zeros(size(Duration));
for i = 1:size(Cumulative_Vol,1)
    end_t = (df.timestamp_ms==t_trials(i+1));
    start_t = (df.timestamp_ms==t_trials(i));
    Cumulative_Vol(i) = df.vol_ul(end_t) - df.vol_ul(start_t);
end

n_rep = 50;
t_cal = table(Duration,Cumulative_Vol);
t_cal.Cumulative_Vol = t_cal.Cumulative_Vol/n_rep;

close all
ax1 = draw.jaxes;
ax1.Position = [0.2,0.2,0.3,0.3];
plot(ax1,t_cal.Duration,t_cal.Cumulative_Vol,'o');
ylabel("Dispensed Volume (uL)")
xlabel("Pump on duration (ms)")
ylim([0,25])

%% Fitting
% Fit best line (y = m*x + b)
p = polyfit(t_cal.Duration, t_cal.Cumulative_Vol, 1); % p(1): slope, p(2): intercept

% Predicted values
y_fit = polyval(p, t_cal.Duration);

% Calculate percentage error (Mean Absolute Percentage Error, MAPE)
mape = mean(abs((t_cal.Cumulative_Vol - y_fit) ./ t_cal.Cumulative_Vol)) * 100;

% Plot data and fit
close all
ax1 = draw.jaxes;
ax1.Position = [0.2,0.2,0.3,0.3];
plot(ax1, t_cal.Duration*1000, t_cal.Cumulative_Vol, 'o', 'DisplayName', '50 Rep Data');
hold(ax1, 'on');
plot(ax1, t_cal.Duration*1000, y_fit, '-','LineWidth',1.5, 'DisplayName', ...
    sprintf('Fit: y = %.2fx + %.2f', p(1), p(2)));
ylabel("Dispensed Volume (uL)")
xlabel("Pump on duration (ms)")
ylim([0,25])
legend(ax1, 'show')
title(ax1, "Octagon 3 Pump 8-1 Calibration Curve")
grid on