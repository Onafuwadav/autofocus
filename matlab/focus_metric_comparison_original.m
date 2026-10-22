% ORIGINAL DISSERTATION SCRIPT
% "MATLAB Code for Focus Metric and Normalisation Comparison"
% (Appendix A of "Towards an Automated Autofocus System for Phonon
% Microscopy: Metric Selection and System Design").
%
% This is the script that produced the dissertation results. The only
% change from the appendix listing is the dataset path: the original used
% 'Dataset\Magnification-2(size)\' relative to the working directory. It
% now resolves to ../data/Magnification-2(size)/ relative to this file, so
% it runs from any working directory and on any OS.
%
% Requires the Image Processing Toolbox (fspecial, imfilter, imgradientxy,
% mat2gray, stretchlim, imadjust).

clc;
clear;
close all;

%% =====================================================
% DATASET SETTINGS
%% =====================================================

brightnessFolders = {'Bright','Normal','Dim'};

% Original: baseFolder = 'Dataset\Magnification-2(size)\';
baseFolder = fullfile(fileparts(mfilename('fullpath')), ...
    '..', 'data', 'Magnification-2(size)');

%% =====================================================
% NORMALISATION METHODS
%% =====================================================

normMethods = {'Raw','Mean','MinMax','ContrastStretch'};

%% =====================================================
% FOCUS METRICS
%% =====================================================

metricNames = {'Laplacian','Tenengrad','Brenner','FFT'};

%% =====================================================
% CREATE STORAGE
%% =====================================================

results = struct();

%% =====================================================
% LOOP THROUGH BRIGHTNESS CONDITIONS
%% =====================================================

for b = 1:length(brightnessFolders)

    brightnessName = brightnessFolders{b};

    folder = fullfile(baseFolder, brightnessName);

    files = dir(fullfile(folder,'*.png'));

    numImages = length(files);

    fprintf('\n================================================\n');
    fprintf('TESTING: %s\n', brightnessName);
    fprintf('================================================\n');

    %% Storage for focus curves

    focusScores = zeros(numImages, ...
        length(normMethods), ...
        length(metricNames));

    elapsedTime = zeros(numImages, length(normMethods), length(metricNames));

    %% =================================================
    % PROCESS IMAGE STACK
    %% =================================================

    for k = 1:numImages

        %% Load image
        img = imread(fullfile(folder, files(k).name));

        %% Convert to grayscale
        if size(img,3) == 3
            imgGray = rgb2gray(img);
        else
            imgGray = img;
        end

        %% Convert to double
        imgGray = double(imgGray);

        %% =================================================
        % NORMALISATION METHODS
        %% =================================================

        for n = 1:length(normMethods)

            method = normMethods{n};

            switch method

                %% RAW
                case 'Raw'

                    imgNorm = imgGray;

                %% MEAN NORMALIZATION
                case 'Mean'

                    imgNorm = imgGray / mean(imgGray(:));

                %% MIN MAX
                case 'MinMax'

                    minVal = min(imgGray(:));
                    maxVal = max(imgGray(:));

                    if maxVal-minVal == 0
                        imgNorm = zeros(size(imgGray));
                    else
                        imgNorm = (imgGray-minVal) / ...
                                  (maxVal-minVal);
                    end

                %% CONTRAST STRETCHING
                case 'ContrastStretch'

                    imgScaled = mat2gray(imgGray);

                    limits = stretchlim(imgScaled,[0.01 0.99]);

                    imgNorm = imadjust(imgScaled, limits, []);

            end

            %% =================================================
            % FOCUS METRICS
            %% =================================================

            for m = 1:length(metricNames)

                metric = metricNames{m};
                
                tStart = tic;

                switch metric

                    %% -----------------------------------------
                    % LAPLACIAN
                    %% -----------------------------------------
                    case 'Laplacian'

                        lapFilter = fspecial('laplacian',0.2);

                        lapImg = imfilter(imgNorm, ...
                                          lapFilter, ...
                                          'replicate');

                        score = var(lapImg(:));

                    %% -----------------------------------------
                    % TENENGRAD
                    %% -----------------------------------------
                    case 'Tenengrad'

                        [Gx,Gy] = imgradientxy(imgNorm,'sobel');

                        score = mean(Gx(:).^2 + Gy(:).^2);

                    %% -----------------------------------------
                    % BRENNER
                    %% -----------------------------------------
                    case 'Brenner'

                        diffImg = imgNorm(:,3:end) - ...
                                  imgNorm(:,1:end-2);

                        score = sum(diffImg(:).^2);

                    %% -----------------------------------------
                    % FFT
                    %% -----------------------------------------
                    case 'FFT'

                        F = fft2(imgNorm);

                        Fshift = fftshift(F);

                        magnitude = abs(Fshift);

                        % Remove low-frequency center region
                        [rows, cols] = size(magnitude);

                        cx = round(cols/2);
                        cy = round(rows/2);

                        radius = 30;

                        magnitude(cy-radius:cy+radius, ...
                                  cx-radius:cx+radius) = 0;

                        score = sum(magnitude(:));

                end
                
                elapsedTime(k,n,m) = toc(tStart); 

                %% Store score
                focusScores(k,n,m) = score;

            end
        end
    end

    fprintf('\nAVERAGE TIME PER METRIC (s):\n');
    for m = 1:length(metricNames)
        fprintf('%s: %.6f\n', metricNames{m}, mean(elapsedTime(:,:,m), 'all'));
    end

    %% =================================================
    % PLOT RESULTS
    %% =================================================

    figure('Name',brightnessName);

    plotIndex = 1;

    for m = 1:length(metricNames)

        subplot(2,2,m);

        hold on;

        for n = 1:length(normMethods)

            plot(focusScores(:,n,m), ...
                'LineWidth',2);

        end
        
        set(gca,'YScale','log');

        title(metricNames{m});

        xlabel('Image Number');
        ylabel('Focus Score');

        legend(normMethods);

        grid on;

    end

    %% =================================================
    % FIND BEST RESULTS
    %% =================================================

    fprintf('\nBEST RESULTS:\n');

    for m = 1:length(metricNames)

        fprintf('\n%s\n', metricNames{m});

        for n = 1:length(normMethods)

            [bestScore, bestIdx] = ...
                max(focusScores(:,n,m));

            fprintf('%s -> ', normMethods{n});

            fprintf('Best Image: %s | ', ...
                files(bestIdx).name);

            fprintf('Best Score: %.4f | ', bestScore);

            fprintf('Mean: %.4f\n', mean(focusScores(:, n, m)));

        end
    end

    %% Store results
    results.(brightnessName) = focusScores;

end