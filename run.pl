#!/usr/bin/perl

use strict;
use warnings;
use File::Basename;
use Math::BigFloat;
use Config::IniFiles;

#my @ARGV;
my $d = dirname(__FILE__);
my $cfg = Config::IniFiles->new( -file => $ARGV[0]);

my $name = $cfg->val('Parameters','name');
my $rad = $cfg->val('Parameters','radius (um)');
my $thk = $cfg->val('Parameters','thickness (um)');
my $stretch = $cfg->val('Parameters','stretch (-)');
my $stiff = $cfg->val('Parameters','stiffness (nm^-1)');
my $pres = $cfg->val('Parameters','gpressure (mpa)');
my $tol = $cfg->val('Parameters','thickness tolerance (%)');
my $dtol = $cfg->val('Parameters','multiplier tolerance (%)');
my $stol = $cfg->val('Parameters','stiffness tolerance (%)');
my $inddepth = $cfg->val('Parameters','indentor depth (um)');

my $tgiv = $cfg->val('Parameters','Thickness multiplier (-)');
my $dgiv = $cfg->val('Parameters','Modulus multiplier (-)');

system("mkdir -p $d/output/$name");
my $tmult; my $dmult; my $flag = 0;

if (defined ($tgiv)){
	$tmult = $tgiv;
	$flag = 1;
} else {
	$tmult = 100;
}

if (defined ($dgiv)){
	$dmult = $dgiv;
	$flag = 2;
} else {
	$dmult = 115;
}

my $npres = $pres*100; my $time = 0.5;
my $ih = 100000; my $il = 100000;

my $num = 0;
while ($flag == 0){
	my $jobname = "P$npres\_M$dmult\_H$tmult";	
	my $dir_path = "$d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/$jobname";
	print $dir_path;

	print "\n\nExpansion trial ", $num, "\n";
	system("nice -10 abaqus cae noGUI=main.py -- $ARGV[0] $flag $npres $dmult $tmult $ih $il");
	system("nice -10 abaqus cae noGUI=write.py -- $ARGV[0] $flag $npres $dmult $tmult");

	open(my $f, "$dir_path/expand.dat") or die ("\nERROR: EXPANSION FILE NOT FOUND!\n\n");
	my $first = <$f>; my $last = $first;
	while (<$f>) {$last= $_}; close $f;
	my @valo = split(/\s/,$last);
	my @vali = split(/\s/,$first);

	if ($valo[0] < $time || $num == 10) {print "\nERROR: EXPANSION NO CONVERGENCE\n\n"; last;}

	my $tratio = int(($thk/$valo[2]));
	if ($tratio < 1e3-$tol*1e1 || $tratio > 1e3+$tol*1e1){
		$tmult = int($tmult * $tratio * 1e-3 + 0.5);
	} elsif ($valo[0] >= $time) {
		print "Expansion complete\n\n"; $flag = 1;
	}				
	print "Tmult ", $tmult, "\nTratio ", $tratio, "\n";
	$num++;
}
	
$num = 0;
while ($flag == 1){	
	print "\nMultiplier trial ", $num, "\n";
	system("nice -10 abaqus cae noGUI=main.py -- $ARGV[0] $flag $npres $dmult $tmult $ih $il");
	system("nice -10 abaqus cae noGUI=write.py -- $ARGV[0] $flag $npres $dmult $tmult");	

	my $jobname = "P$npres\_M$dmult\_H$tmult";	
	my $dir_path = "$d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/$jobname";	
	print $dir_path;

	open(my $f, "$dir_path/expand.dat") or die ("\nERROR: EXPANSION FILE NOT FOUND!\n\n");
	my $first = <$f>; my $last = $first;
	while (<$f>) {$last= $_}; close $f;
	my @valo = split(/\s/,$last);
	my @vali = split(/\s/,$first);
		
	if ($valo[0] < $time || $num == 10) {print "\nERROR: MULTIPLIER NO CONVERGENCE\n\n"; last;}
		
	my $dratio = int(1e3*($valo[1]/$vali[1] - 1.0)/($stretch - 1.0) + 0.5);
	if ($dratio < (1e3-$dtol*1e1) || $dratio > (1e3+$dtol*1e1)){
		$dmult = int($dmult * $dratio * 1e-3 + 0.5);
	}  else {
		print "\nMultiplier complete\n\n"; $flag = 3; $ih =  int($valo[1]*1e6); $il = int($valo[3]*1e6); print "\nh ", $ih, "\nl ", $il; last;
	}
	print "\nDmult ", $dmult, "\nDratio ", $dratio, "\n";
	$num++;
}

system("rm -rf $d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/*");

while ($flag == 2){	
	print "\nPosition trial ", $num, "\n";
	system("nice -10 abaqus cae noGUI=main.py -- $ARGV[0] $flag $npres $dmult $tmult $ih $il");
	system("nice -10 abaqus cae noGUI=write.py -- $ARGV[0] $flag $npres $dmult $tmult");	

	my $jobname = "P$npres\_M$dmult\_H$tmult";	
	my $dir_path = "$d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/$jobname";	
	print $dir_path;

	open(my $f, "$dir_path/expand.dat") or die ("\nERROR: EXPANSION FILE NOT FOUND!\n\n");
	my $first = <$f>; my $last = $first;
	while (<$f>) {$last= $_}; close $f;
	my @valo = split(/\s/,$last);
	my @vali = split(/\s/,$first);
		
	if ($valo[0] < $time) {print "\nERROR: MULTIPLIER NO CONVERGENCE\n\n"; last;}
	print "\nPosition complete\n\n"; $flag = 3; $ih =  int($valo[1]*1e6); $il = int($valo[3]*1e6); print "\nh ", $ih, "\nl ", $il; last;
}

$num = 0;
while ($flag == 3){
	my $jobname = "P$npres\_M$dmult\_H$tmult";	
	my $dir_path = "$d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/$jobname";
	
	print "\nIndent trial ", $num, "\n";
	system("nice -10 abaqus cae noGUI=main.py -- $ARGV[0] $flag $npres $dmult $tmult $ih $il");	
	system("nice -10 abaqus cae noGUI=write.py -- $ARGV[0] $flag $npres $dmult $tmult");
	system("python analysis.py $ARGV[0] $npres $dmult $tmult");
	
	my $res = Config::IniFiles->new( -file => "$dir_path/result.dat");
	my $simstiff = $res->val("Output","simulated stiffness (nm^-1)");
	my $simdepth = $res->val("Output","simulated depth (um)");
	
	if ($simdepth < $inddepth*0.25 || $num == 10) {print "\nERROR: INDENTATION NO CONVERGENCE\n\n"; last;}
	
	my $pratio = int(1e2*$stiff/$simstiff + 0.5);
	if ($pratio < (1e2-$stol) || $pratio > (1e2+$stol)){
		$npres = int($npres * $pratio * 1e-2 + 0.5);	
	} else {
		print "\nIndent complete\n\n"; $flag = 3; system("cp $dir_path/result.dat $d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/final_result.dat"); 
		system("cp $dir_path/indent.dat $d/output/$name/R$rad\_T$thk\_A$stiff\_S$stretch/final_indent.dat");
		last;
	}
	print "\nPressure ", $npres, "\nPratio ", $pratio, "\n";
	$num++;
}
	
system("rm -rf $d/abaqus*");

