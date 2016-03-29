#! /usr/bin/perl -w
# PotAncG2_2.pl -- MySQL:GenealogyCL:ivv7srv16.uni-muenster.de
# generates 9 general PotAncCL.<PotAnc> tables from the 9 GenealogyCL.<GenTab> tables for CBGM 2.0
# generates (now) 28 ECM_Acts_PotAnc.05NNPotAnc tables from the ECM_Acts_VG.05NNGenTab_2 tables
# Vorlage von Klaus Wachtel, Anpassung von Volker Krüger

#@ _USE_
use strict;
use DBI;
use access;

my $DEBUG = 0;
my $cmd;

### data source names
my $dsn = "DBI:mysql:ECM_Acts_VG:localhost";
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

#@ _CONNECT_


my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0 });

my ($sql, $table);
my $source1 = '`ECM_Acts_Mss`.`ActsMsList`';

### empty target table
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`05".$chnstr."PotAnc`");

$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0501PotAnc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0502PotAnc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0503PotAnc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0504PotAnc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0505PotAnc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0506PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0507PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0508PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0509PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0510PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0511PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0512PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0513PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0514PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0515PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0516PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0517PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0518PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0519PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0520PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0521PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0522PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0523PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0524PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0525PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0526PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0527PotAnc`");
#$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAnc`.`0528PotAnc`");

my (@mss, @ary, @msl, @writary, @wlist, $sth, $ary, $writary, $ms, $bs, $bsn);

###1 fetch an array of mss from CLMsList
###2 loop through the ms array to fetch @wlist row by row
	
$sql = "SELECT `MS` FROM $source1 WHERE `MS` < 400000 ";
# FIXME BEGIN
# as long as not all chapters have been processed
# the script is limited to the chapters which are already finished.
$sql .= "AND (`Apg01` = 1 ";
$sql .= "OR   `Apg02` = 1 ";
$sql .= "OR   `Apg03` = 1 ";
$sql .= "OR   `Apg04` = 1 ";
$sql .= "OR   `Apg05` = 1 ";
$sql .= "OR   `Apg06` = 1) ";
# FIXME END
if ($DEBUG) { print __LINE__.": ".$sql."\n" };
$sth = $dbh->prepare ($sql);
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
	unless ($ary[0]==1)
	{
		@msl = (@msl, @ary);
	}
} 

foreach $_ (@msl) 
{
	$ms=$_;
	if ($DEBUG) { print "\nbehandelte Handschrift: $ms\n"; }
	(@writary) = $dbh->selectrow_array("SELECT * FROM $source1 WHERE `MS` = $_"); # ECM_Acts_Mss.ActsMsList

#0: id, 1: check, 2: witn(varchar), 3: ms(int), 4: Apg01, ..., 31: Apg28, 32: Apg

	@wlist=();
	if ($writary[32]==1) # it is a complete manuscript
	{
		##if $ms contains all chapters of Acts
		@wlist = ('0501GenTab_2'
				 , '0502GenTab_2'
				 , '0503GenTab_2'
				 , '0504GenTab_2'
				 , '0505GenTab_2'
				 , '0506GenTab_2'
# 				 , '0507GenTab_2'
# 				 , '0508GenTab_2'
# 				 , '0509GenTab_2'
# 				 , '0510GenTab_2'
# 				 , '0511GenTab_2'
# 				 , '0512GenTab_2'
# 				 , '0513GenTab_2'
# 				 , '0514GenTab_2'
# 				 , '0515GenTab_2'
# 				 , '0516GenTab_2'
# 				 , '0517GenTab_2'
# 				 , '0518GenTab_2'
# 				 , '0519GenTab_2'
# 				 , '0520GenTab_2'
# 				 , '0521GenTab_2'
# 				 , '0522GenTab_2'
# 				 , '0523GenTab_2'
# 				 , '0524GenTab_2'
# 				 , '0525GenTab_2'
# 				 , '0526GenTab_2'
# 				 , '0527GenTab_2'
# 				 , '0528GenTab_2' 
				 );
		# add tables
		# in order to get total sums 
		# with and without fragments
		@wlist = (@wlist, '0529GenTab_2', '0530GenTab_2');
		if ($DEBUG) { print "$ms hat Text in allen Kapiteln\n"; }
	} 
	else # $writary[32]==0 # decide chapter by chapter
	{
		if ($writary[4]==1) {
			@wlist = (@wlist, '0501GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 1\n"; }
		}
		if ($writary[5]==1) {
			@wlist = (@wlist, '0502GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 2\n"; }
		}
		if ($writary[6]==1) {
			@wlist = (@wlist, '0503GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 3\n"; }
		}
		if ($writary[7]==1) {
			@wlist = (@wlist, '0504GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 4\n"; }
		}
		if ($writary[8]==1) {
			@wlist = (@wlist, '0505GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 5\n"; }
		}
		if ($writary[9]==1) {
			@wlist = (@wlist, '0506GenTab_2');
			if ($DEBUG) { print "$ms hat Text in Kapitel 6\n"; }
		}
#		if ($writary[10]==1) {
#			@wlist = (@wlist, '0507GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 7\n"; }
#		}
#		if ($writary[11]==1) {
#			@wlist = (@wlist, '0508GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 8\n"; }
#		}
#		if ($writary[12]==1) {
#			@wlist = (@wlist, '0509GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 9\n"; }
#		}
#		if ($writary[13]==1) {
#			@wlist = (@wlist, '0510GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 10\n"; }
#		}
#		if ($writary[14]==1) {
#			@wlist = (@wlist, '0511GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 11\n"; }
#		}
#		if ($writary[15]==1) {
#			@wlist = (@wlist, '0512GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 12\n"; }
#		}
#		if ($writary[16]==1) {
#			@wlist = (@wlist, '0513GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 13\n"; }
#		}
#		if ($writary[17]==1) {
#			@wlist = (@wlist, '0514GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 14\n"; }
#		}
#		if ($writary[18]==1) {
#			@wlist = (@wlist, '0515GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 15\n"; }
#		}
#		if ($writary[19]==1) {
#			@wlist = (@wlist, '0516GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 16\n"; }
#		}
#		if ($writary[20]==1) {
#			@wlist = (@wlist, '0517GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 17\n"; }
#		}
#		if ($writary[21]==1) {
#			@wlist = (@wlist, '0518GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 18\n"; }
#		}
#		if ($writary[22]==1) {
#			@wlist = (@wlist, '0519GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 19\n"; }
#		}
#		if ($writary[23]==1) {
#			@wlist = (@wlist, '0520GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 20\n"; }
#		}
#		if ($writary[24]==1) {
#			@wlist = (@wlist, '0521GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 21\n"; }
#		}
#		if ($writary[25]==1) {
#			@wlist = (@wlist, '0522GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 22\n"; }
#		}
#		if ($writary[26]==1) {
#			@wlist = (@wlist, '0523GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 23\n"; }
#		}
#		if ($writary[27]==1) {
#			@wlist = (@wlist, '0524GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 24\n"; }
#		}
#		if ($writary[28]==1) {
#			@wlist = (@wlist, '0525GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 25\n"; }
#		}
#		if ($writary[29]==1) {
#			@wlist = (@wlist, '0526GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 26\n"; }
#		}
#		if ($writary[30]==1) {
#			@wlist = (@wlist, '0527GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 27\n"; }
#		}
#		if ($writary[31]==1) {
#			@wlist = (@wlist, '0528GenTab_2');
#			if ($DEBUG) { print "$ms hat Text in Kapitel 28\n"; }
#		}
		# add table all chapter incl. fragments 
		# in order to get total sums 
		@wlist = (@wlist, '0530GenTab_2');
	}
	
	for (@wlist) 
	{
		$bs = $_;
		if ($DEBUG) { print "bs ist $bs\n" };
		if ($bs eq '0501GenTab_2') { 
			$bsn=1;  
			$table="0501PotAnc"; 
		}
		if ($bs eq '0502GenTab_2') { 
			$bsn=2;  
			$table="0502PotAnc";
		}
		if ($bs eq '0503GenTab_2') { 
			$bsn=3;
			$table="0503PotAnc";  
		}
		if ($bs eq '0504GenTab_2') { 
			$bsn=4;  
			$table="0504PotAnc";  
		}
		if ($bs eq '0505GenTab_2') { 
			$bsn=5;  
			$table="0505PotAnc";  
		}
		if ($bs eq '0506GenTab_2') { 
			$bsn=6;  
			$table="0506PotAnc";  
		}
		if ($bs eq '0507GenTab_2') { 
			$bsn=7;  
			$table="0507PotAnc";  
		}
		if ($bs eq '0508GenTab_2') { 
			$bsn=8;  
			$table="0508PotAnc";  
		}
		if ($bs eq '0509GenTab_2') { 
			$bsn=9;  
			$table="0509PotAnc";  
		}
		if ($bs eq '0510GenTab_2') { 
			$bsn=10; 
			$table="0510PotAnc";  
		}
		if ($bs eq '0511GenTab_2') { 
			$bsn=11; 
			$table="0511PotAnc";  
		}
		if ($bs eq '0512GenTab_2') { 
			$bsn=12; 
			$table="0512PotAnc";  
		}
		if ($bs eq '0513GenTab_2') { 
			$bsn=13; 
			$table="0513PotAnc";  
		}
		if ($bs eq '0514GenTab_2') { 
			$bsn=14; 
			$table="0514PotAnc";  
		}
		if ($bs eq '0515GenTab_2') { 
			$bsn=15; 
			$table="0515PotAnc";  
		}
		if ($bs eq '0516GenTab_2') { 
			$bsn=16; 
			$table="0516PotAnc";  
		}
		if ($bs eq '0517GenTab_2') { 
			$bsn=17; 
			$table="0517PotAnc";  
		}
		if ($bs eq '0518GenTab_2') { 
			$bsn=18; 
			$table="0518PotAnc";  
		}
		if ($bs eq '0519GenTab_2') { 
			$bsn=19; 
			$table="0519PotAnc";  
		}
		if ($bs eq '0520GenTab_2') { 
			$bsn=20; 
			$table="0520PotAnc";  
		}
		if ($bs eq '0521GenTab_2') { 
			$bsn=21; 
			$table="0521PotAnc";  
		}
		if ($bs eq '0522GenTab_2') { 
			$bsn=22; 
			$table="0522PotAnc";  
		}
		if ($bs eq '0523GenTab_2') { 
			$bsn=23; 
			$table="0523PotAnc";  
		}
		if ($bs eq '0524GenTab_2') { 
			$bsn=24; 
			$table="0524PotAnc";  
		}
		if ($bs eq '0525GenTab_2') { 
			$bsn=25; 
			$table="0525PotAnc";  
		}
		if ($bs eq '0526GenTab_2') { 
			$bsn=26; 
			$table="0526PotAnc";  
		}
		if ($bs eq '0527GenTab_2') { 
			$bsn=27; 
			$table="0527PotAnc";  
		}
		if ($bs eq '0528GenTab_2') { 
			$bsn=28; 
			$table="0528PotAnc";  
		}
		if ($bs eq '0529GenTab_2') { 
			$bsn=29; 
			$table="0529PotAnc";  
		}
		if ($bs eq '0530GenTab_2') { 
			$bsn=30; 
			$table="0530PotAnc";  
		}

#######################
###Subroutine PotAnc###
#######################

		sub PotAnc;
		PotAnc;

### Each 'PotAncestors' now has to be appended to the appropriate table as prepared in 'PotAncCL'
### 'PotAncCL' is a database containing 9 tables: 1-7 Jas/.../JdPotAnc, 8 CL1PotAnc, 9CL2PotAnc. 
### CL1PotAnc: values summarised for all CL excluding fragments
### CL2PotAnc: values summarised for all CL including fragments

		#$dbh->do ("TRUNCATE `ECM_Acts_PotAnc`.`$table`; "); # truncate one time only: beginning of the script

		$dbh->do ("INSERT INTO `ECM_Acts_PotAnc`.`$table` 
						SELECT * FROM `ECM_Acts_VG`.`PotAncestors` ;");
		if ($DEBUG) {
			print "\n".__LINE__."INSERT INTO `ECM_Acts_PotAnc`.`$table` SELECT * FROM `ECM_Acts_VG`.`PotAncestors` ;"
		}
	}  #for (@wlist)

}  #foreach $_ (@msl)

$sth->finish ();

$dbh->disconnect ();

exit (0);

####################################################################################################

sub PotAnc 
{
	if ($DEBUG) { print __LINE__."bsn ist $bsn\n"; }

	my @arymin;
	my $min=0;			# will be used for defining the threshold value
	my $dec;			# for sequencing pot. ancestors
	#my $sth;

	# 300350 is a complete ms in CL. Therefore the number of passages for which $ms and 300350 are
	# both exstant indicates the total of passages at which $ms is extant.
	# (The number of passages that $ms shares with A would be misleading, because A is treated
	# as lacking where it is left open whether a or another reading is initial.)
	# For Acts: According to ECM_Acts_Mss.ActsMsListVal the mss 945 and 808 have the highest sum of
	# text passages apart from the Ausgangstext. 
	my $cmd;
	if ($ms != 309450) {
		$cmd = "SELECT PASSAGES FROM `ECM_Acts_VG`.`$bs` WHERE (MS1='$ms' AND MS2='309450') OR (MS1='309450' AND MS2='$ms')";
	} else {
		$cmd =  "SELECT PASSAGES FROM `ECM_Acts_VG`.`$bs` WHERE (MS1='$ms' AND MS2='308080') OR (MS1='308080' AND MS2='$ms')";
	}
	if ($DEBUG) { print __LINE__ . $cmd . "\n"; }
	$sth = $dbh->prepare($cmd);
	$sth->execute();

	@arymin = $sth->fetchrow_array(); # no while loop necessary
	$min=$arymin[0];
	if ($DEBUG) { print __LINE__.": min is: ".$min."\n"; }

				 # $min is an integer but
	$min=$min/2; # result may be a float

	if ($min==0) {
		print "\n$ms not extant in \n$bsn $bs\n\n";
		$sth->finish ();
		$dbh->disconnect ();
		exit (2);
	}


	# define decimal places for rounding values in PERC1 needed for sequencing pot. ancestors
	# a single chapter gets two digits after the decimal separator,
	# all chapters get three digits after the decimal separator

	if ($bsn<29) {
		$dec="2f";
	} else {
		$dec="3f";
	}

	$dbh->do ("TRUNCATE TABLE `ECM_Acts_VG`.`TempTab`");

	$dbh->do ("INSERT INTO `ECM_Acts_VG`.`TempTab` 
						SELECT  * FROM `ECM_Acts_VG`.`$bs` 
						WHERE (MS1='$ms' AND (DIR='<--' OR DIR=' ')) OR (MS2='$ms' AND (DIR='-->' OR DIR=' '))
						");



	$sth = $dbh->prepare ("SELECT WITN1, WITN2, DIR, MS1, MS2, W1FW2, W1TW2, PERC2, PERC3 FROM `ECM_Acts_VG`.`TempTab`");
	$sth->execute();

	### $ms will take the place of WITN1/MS1 in all rows. The content of all relevant fields 
	### is transposed accordingly.
	### 'fetchrow' triggers fields in the following sequence:
	###	$ary[0] WITN1, [1] WITN2, [2] DIR, [3] MS1, [4] MS2, [5] W1FW2, [6] W1TW2, [7] PERC2, [8] PERC3.

	#my @ary;

	while (@ary = $sth->fetchrow_array())
	{
		
		if ($ary[4]=$ms) {
		
			$dbh->do ("UPDATE `ECM_Acts_VG`.`TempTab` SET
					WITN2='$ary[0]',
					WITN1='$ary[1]',
					MS2='$ary[3]',
					MS1='$ary[4]',
					W1FW2='$ary[6]',
					W1TW2='$ary[5]',
					PERC2='$ary[8]',
					PERC3='$ary[7]'
					WHERE MS1='$ary[3]' AND MS2='$ary[4]';");
		 }
		 
		 if ($ary[2] eq '-->') {
		 
		 $dbh->do ("UPDATE `ECM_Acts_VG`.`TempTab` SET DIR='<--'
					WHERE MS1='$ary[4]' AND MS2='$ary[3]';");
		}
		 
		 if ($ary[2] eq '<--') {
		 
		 $dbh->do ("UPDATE `ECM_Acts_VG`.`TempTab` SET DIR='-->'
					WHERE MS1='$ary[4]' AND MS2='$ary[3]';");
		}
		
	} # while

	$dbh->do ("TRUNCATE TABLE `ECM_Acts_VG`.`PotAncestors`");

	$dbh->do ("INSERT INTO `ECM_Acts_VG`.`PotAncestors` 
					SELECT  WITN1, DIR, WITN2, NR, MS1, MS2, PERC1, EQ, PERC2, W1FW2, PERC3, 
					W1TW2, PERC4, UNCLEAR, NOREL, PASSAGES 
					FROM `ECM_Acts_VG`.`TempTab` 
					ORDER BY `PERC1` DESC, `MS2` ASC ");


	### number pot. ancestors

	my $msa=1;
	my $msb=1;
	my $count=1;
	my $perc1;
	my @ary3;


	$sth = $dbh->prepare ("SELECT * FROM `ECM_Acts_VG`.`PotAncestors`
								#0 WITN1, 1 DIR, 2 WITN2, 3 NR, 6 PERC1, 7 EQ, 15 STELLEN ");
	$sth->execute();

	##$rounded = sprintf("%.2f"", $unrounded);

	while (@ary3=$sth->fetchrow_array()) 
	{
		if ($ary3[1] eq '<--' and $ary3[15]>$min) 
		{ 	
			##The ms compared with $ms will be counted as pot. ancestor only if the number of passages 
			##extant in both mss exceeds the threshold value $min. Thus the program will look for potential
			##ancestors of small fragments, but will exclude them from comparison when it looks for pot.
			##ancestors of more extensive documents. The reason is that small fragments have a much higher
			##chance to reach high percentages of agreement and priority when compared with fuller mss.
			if ($count == 1) {
				$perc1 = sprintf("%.$dec", $ary3[6]);			##round to decimal places according to
				$count++;										##selected base ($bs)
				$dbh->do ("UPDATE `ECM_Acts_VG`.`PotAncestors` SET	
							NR='$msa'
							WHERE WITN2='$ary3[2]';");
			} else {	
			
				if (sprintf("%.$dec", $ary3[6]) == $perc1)  {
					$msb++;
					$dbh->do ("UPDATE `ECM_Acts_VG`.`PotAncestors` SET
								NR='$msa'
								WHERE WITN2='$ary3[2]';");
				} else {
					$perc1=sprintf("%.$dec", $ary3[6]);
					$msb++;
					$msa=$msb;
					$dbh->do ("UPDATE `ECM_Acts_VG`.`PotAncestors` SET
								NR='$msa'
								WHERE WITN2='$ary3[2]';");
				}
			}
		}	
	}  # while

}  # sub PotAnc
