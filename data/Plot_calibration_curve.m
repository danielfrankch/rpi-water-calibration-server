% Select CSV file via file explorer
[file, path] = uigetfile('*.csv', 'Select CSV file');
if isequal(file,0)
    error('No file selected.');
end

% Read CSV into table
df = readtable(fullfile(path, file));

%%
% Plot_locations = [61,60,51,42,33,25,18,11,4,5,14,23,32,40,47,54];
close all
for i = 1:16
    subplot(4,4,i)
    dff = df(df.valve==i,3:4);
    x = dff{:,1} * 1000;
    y = dff{:,2} * 1000;
    plot(x,y,'o')
    title(sprintf('Pump %d',i))
    xlim([0,40])
    ylim([0,9])

    hold on
    % Linear regression
    p = polyfit(x, y, 1);
    xx = linspace(min(x), max(x), 100);
    yy = polyval(p, xx);
    plot(xx, yy, 'r','LineWidth',1)
    hold off

    % Solve for x when y = 2.5 using the linear fit
    y_target = 2.5;
    x_interp = (y_target - p(2)) / p(1);
    
    % Overlay as text
    text(2.5, 6.5, ...
         sprintf('%.2f ms, 2.5uL', x_interp), ...
         'VerticalAlignment','bottom', ...
         'HorizontalAlignment','left',...
         'FontSize',8);
    
end

subplot(4,4,13)
ylabel("Volume Dispensed (uL)")
subplot(4,4,16)
xlabel("Pump Activation Time (ms)")
sgtitle('Octagon 267001 auto water calibration')