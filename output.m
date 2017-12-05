clear all
close all

hold on
c = ['b', 'g', 'm', 'k','r'];
P = 20;
%stretch = [1.161 1.195 1.289 1.307 1.192];
%rad = [7.78 2.73 2.59 2.94 3.19];
%thick = [200 137.5 290.5 198.6 273.5];
M = 81;
type = 4;

%a = a+1;
for i=0:0
        f = '/home/gautam/bin/Abaqus_data/Christina/Christina';
        file = [f num2str(type) '/outputm' num2str(i) '/T' num2str(i) '_P' num2str(P) '_M' num2str(M) '/stiff.dat']
        if (exist(file, 'file') == 2)    
            data = load(file);
            time = data(:,1)*1.25e-3;
            movt = data(:,2);
            movb = data(:,3);
            
            fn = data(:,4)*1e2;
            fm = data(:,5); 
            
            force =[]; move=[];
            for k=1:length(fn)
                %if (time(k) < 2.107 && time(k) > 1.45)
                % if (time(k) < 2.327 && time(k) > 1.365)
               % if (fn(k) >= 0 && fn(k) < 8e-6)
                     force = [force fn(k)];              
                     move = [move time(k)];
               % end
                if (isempty(force) == 0 && fn(k) > 3e-6)
                     break;
                end
            end
            move(1:3) = []; force(1:3) = [];
            modulus = polyfit(move, force,1);
           
           % figure
            plot(move,force,[c(i+1) '*'])
            hold on
            plot(move,move*modulus(1)+modulus(2),'r')
            modulus = modulus*1e3
        else
            disp(file);
        end
    %    fitter(j) = fit(1);
end
