#! /usr/bin/perl -w
# PotDescG2_2.pl -- MySQL:GenealogyCL:ivv7srv16.uni-muenster.de
# generates 9 general PotDescCL.<PotDesc> tables from the 9 GenealogyCL.<GenTab> tables for CBGM 2.0
# Vorlage von Klaus Wachtel, Anpassung für Acta von Volker Krüger

#@ _USE_
use strict;
use DBI;
use access;

### data source names
my $dsn = "DBI:mysql:ECM_Acts_VG:localhost";
my $user_name = getUsername();						# user name
my $password = getPassword();						# password
my $DEBUG = 0;

#@ _CONNECT_

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0 });

my $source1 = '`ECM_Acts_Mss`.`ActsMsList_2`';

$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0501PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0502PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0503PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0504PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0505PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0506PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0507PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0508PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0509PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0510PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0511PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0512PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0513PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0514PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0515PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0516PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0517PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0518PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0519PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0520PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0521PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0522PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0523PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0524PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0525PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0526PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0527PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0528PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0529PotDesc`");
$dbh->do ("TRUNCATE TABLE `ECM_Acts_PotAncPh3`.`0530PotDesc`");

my (@mss, @ary, @msl, @writary, @wlist, $sth, $ary, $writary, $ms, $bs, $bsn);

###1 fetch an array of mss from ECM_Acts_Mss.ActsMsList
###2 loop through the ms array to fetch @wlist row by row

$sth = $dbh->prepare ("SELECT `MS` FROM $source1 WHERE 1"); # $source1 = ECM_Act_Mss.ActsMsList;
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
} 

foreach $_ (@msl) 
{
	if ($DEBUG) {
		print "ms: $_\n";
	}
	
	$ms=$_;
	(@writary) = $dbh->selectrow_array("SELECT * FROM $source1 WHERE `MS` = $_ "); # $source1 = ECM_Act_Mss.ActsMsList;

	@wlist=();
	if ($writary[32]) 
	{	##if $ms contains all chapters
		@wlist = (
				    '0501GenTab_2'
				  , '0502GenTab_2'
				  , '0503GenTab_2'
				  , '0504GenTab_2'
				  , '0505GenTab_2'
				  , '0506GenTab_2'
 				  , '0507GenTab_2'
 				  , '0508GenTab_2'
 				  , '0509GenTab_2'
 				  , '0510GenTab_2'
 				  , '0511GenTab_2'
 				  , '0512GenTab_2'
 				  , '0513GenTab_2'
 				  , '0514GenTab_2'
 				  , '0515GenTab_2'
 				  , '0516GenTab_2'
 				  , '0517GenTab_2'
 				  , '0518GenTab_2'
 				  , '0519GenTab_2'
 				  , '0520GenTab_2'
 				  , '0521GenTab_2'
 				  , '0522GenTab_2'
 				  , '0523GenTab_2'
 				  , '0524GenTab_2'
 				  , '0525GenTab_2'
 				  , '0526GenTab_2'
 				  , '0527GenTab_2'
 				  , '0528GenTab_2'
				  );
		@wlist = (@wlist, '0529GenTab_2', '0530GenTab_2');
	} 
	else #if $ms misses one or more chapters
	{
		if ($writary[4]==1)  { @wlist = (@wlist, '0501GenTab_2'); }
		if ($writary[5]==1)  { @wlist = (@wlist, '0502GenTab_2'); }
		if ($writary[6]==1)  { @wlist = (@wlist, '0503GenTab_2'); }
		if ($writary[7]==1)  { @wlist = (@wlist, '0504GenTab_2'); }
		if ($writary[8]==1)  { @wlist = (@wlist, '0505GenTab_2'); }
		if ($writary[9]==1)  { @wlist = (@wlist, '0506GenTab_2'); }
 		if ($writary[10]==1) { @wlist = (@wlist, '0507GenTab_2'); }
 		if ($writary[11]==1) { @wlist = (@wlist, '0508GenTab_2'); }
 		if ($writary[12]==1) { @wlist = (@wlist, '0509GenTab_2'); }
 		if ($writary[13]==1) { @wlist = (@wlist, '0510GenTab_2'); }
 		if ($writary[14]==1) { @wlist = (@wlist, '0511GenTab_2'); }
 		if ($writary[15]==1) { @wlist = (@wlist, '0512GenTab_2'); }
 		if ($writary[16]==1) { @wlist = (@wlist, '0513GenTab_2'); }
 		if ($writary[17]==1) { @wlist = (@wlist, '0514GenTab_2'); }
 		if ($writary[18]==1) { @wlist = (@wlist, '0515GenTab_2'); }
		if ($writary[19]==1) { @wlist = (@wlist, '0516GenTab_2'); }
 		if ($writary[20]==1) { @wlist = (@wlist, '0517GenTab_2'); }
 		if ($writary[21]==1) { @wlist = (@wlist, '0518GenTab_2'); }
 		if ($writary[22]==1) { @wlist = (@wlist, '0519GenTab_2'); }
 		if ($writary[23]==1) { @wlist = (@wlist, '0520GenTab_2'); }
 		if ($writary[24]==1) { @wlist = (@wlist, '0521GenTab_2'); }
 		if ($writary[25]==1) { @wlist = (@wlist, '0522GenTab_2'); }
 		if ($writary[26]==1) { @wlist = (@wlist, '0523GenTab_2'); }
 		if ($writary[27]==1) { @wlist = (@wlist, '0524GenTab_2'); }
 		if ($writary[28]==1) { @wlist = (@wlist, '0525GenTab_2'); }
 		if ($writary[29]==1) { @wlist = (@wlist, '0526GenTab_2'); }
 		if ($writary[30]==1) { @wlist = (@wlist, '0527GenTab_2'); }
 		if ($writary[31]==1) { @wlist = (@wlist, '0528GenTab_2'); }
	} #else

	for (@wlist) 
	{
		$bs = $_;
		if ($bs eq '0501GenTab_2') { $bsn=1; }
		if ($bs eq '0502GenTab_2') { $bsn=2; }
		if ($bs eq '0503GenTab_2') { $bsn=3; }
		if ($bs eq '0504GenTab_2') { $bsn=4; }
		if ($bs eq '0505GenTab_2') { $bsn=5; }
		if ($bs eq '0506GenTab_2') { $bsn=6; }
 		if ($bs eq '0507GenTab_2') { $bsn=7; }
 		if ($bs eq '0508GenTab_2') { $bsn=8; }
 		if ($bs eq '0509GenTab_2') { $bsn=9; }
 		if ($bs eq '0510GenTab_2') { $bsn=10; }
 		if ($bs eq '0511GenTab_2') { $bsn=11; }
 		if ($bs eq '0512GenTab_2') { $bsn=12; }
 		if ($bs eq '0513GenTab_2') { $bsn=13; }
 		if ($bs eq '0514GenTab_2') { $bsn=14; }
 		if ($bs eq '0515GenTab_2') { $bsn=15; }
 		if ($bs eq '0516GenTab_2') { $bsn=16; }
 		if ($bs eq '0517GenTab_2') { $bsn=17; }
 		if ($bs eq '0518GenTab_2') { $bsn=18; }
 		if ($bs eq '0519GenTab_2') { $bsn=19; }
 		if ($bs eq '0520GenTab_2') { $bsn=20; }
 		if ($bs eq '0521GenTab_2') { $bsn=21; }
 		if ($bs eq '0522GenTab_2') { $bsn=22; }
 		if ($bs eq '0523GenTab_2') { $bsn=23; }
 		if ($bs eq '0524GenTab_2') { $bsn=24; }
 		if ($bs eq '0525GenTab_2') { $bsn=25; }
 		if ($bs eq '0526GenTab_2') { $bsn=26; }
 		if ($bs eq '0527GenTab_2') { $bsn=27; }
 		if ($bs eq '0528GenTab_2') { $bsn=28; }
 		if ($bs eq '0529GenTab_2') { $bsn=29; }
 		if ($bs eq '0530GenTab_2') { $bsn=30; }


########################
###Subroutine PotDesc###
########################

		sub PotDesc;	# Bekanntmachung der Subroutine PotDesc
		PotDesc;		# Aufruf von PotDesc: hier wird die Tabelle PotDescendants gefuellt.

### Each 'PotDescendants' now has to be appended to the appropriate table as prepared in 'CBGM_CL2_PotAnc'
### 'CBGM_CL2_PotAnc' is a database containing 18 tables: 1-7 Jas/.../JdPotAnc/Desc_2, 8 CL1PotAnc/Desc_2, 9CL2PotAnc/Desc_2. 
### CL1PotAnc/Desc_2: values summarised for all CL excluding fragments
### CL2PotAnc/Desc_2: values summarised for all CL including fragments


		if ($bsn==1) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0501PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==2) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0502PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==3) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0503PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==4) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0504PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==5) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0505PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==6) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0506PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==7) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0507PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==8) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0508PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==9) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0509PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==10) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0510PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==11) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0511PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==12) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0512PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==13) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0513PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==14) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0514PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==15) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0515PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==16) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0516PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==17) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0517PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==18) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0518PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==19) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0519PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==20) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0520PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==21) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0521PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==22) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0522PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==23) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0523PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==24) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0524PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==25) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0525PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==26) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0526PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==27) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0527PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==28) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0528PotDesc` 
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");
		}
		if ($bsn==29) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0529PotDesc`
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");	
		}
		if ($bsn==30) {
			$dbh->do ("INSERT INTO `ECM_Acts_PotAncPh3`.`0530PotDesc`
						SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants` ;");	
		}		
	
	}  #for (@wlist)

}  #foreach $_ (@msl)

$sth->finish ();

$dbh->disconnect ();

exit (0);

####################################################################################################
#                                   Definition of sub program                                      #
####################################################################################################
#                                                                                                  #
sub PotDesc {

	my @arymin;
	my $min=0;			# will be used for defining the threshold value
	my $dec;			# for sequencing pot. Descendants

	# 300350 is a complete ms. Therefore the number of passages for which $ms and 300350 are
	# both exstant indicates the total of passages at which $ms is extant.
	# (The number of passages that $ms shares with A would be misleading, because A is treated
	# as lacking where it is left open whether a or another reading is initial.)
	
	# Reference manuscripts for the catholic letters: (1.) 35 and (2.) 617.
	# Reference manuscripts for the Book of Acts: (1.) 945 and (2.) 808.
	# Reference manuscripts for Mark: ...

	if ($ms != 309450) {
		$sth = $dbh->prepare ("SELECT PASSAGES FROM `ECM_Acts_VGPh3`.`$bs` WHERE (MS1='$ms' AND MS2='309450') OR (MS1='309450' AND MS2='$ms')"); # $bs ist z.B. NNGenTab_2
	} else {
		$sth = $dbh->prepare ("SELECT PASSAGES FROM `ECM_Acts_VGPh3`.`$bs` WHERE MS2='$ms' AND MS1='308080'");
	}

	$sth->execute();

	while (@arymin = $sth->fetchrow_array())
	{
		$min=$arymin[0];
	}

	$min=$min/2;

	if ($min==0) {
		print "\n$ms not extant in \n$bsn $bs\n\n";
		$sth->finish ();
		$dbh->disconnect ();
		exit (0);
#	} else {
#	print "\nmin=$min\n";
	}


# define decimal places for rounding values in PERC1 needed for sequencing pot. Descendants
# different definitions take different amount of text (different amount of data) into account
# values in PERC1 are set to equal
# for Jas ... 1Jn as data source: if the values in PERC1 rounded up to the second position after decimal point are equal;
# for 2-3Jn: if the values in PERC1 rounded up to the full number are equal;
# for Jd: if the values in PERC1 rounded up to the first position after decimal point are equal;
# for the entire CL corpus: if the values in PERC1 rounded up to the third position after decimal point are equal.
# The ranking number in PotDesc tables will remain the same accordingly.

	#
	#if ($bsn<5) {
	#	$dec="2f";
	#	} else {
	#	if ($bsn==5 or $bsn==6) {
	#		$dec="0f";
	#		} else {
	#		if ($bsn==7) {
	#			$dec="1f";
	#			} else {
	#			$dec="3f";
	#		}
	#	}
	#}

# For Acts we take one value only:
	$dec = "3f";


	$dbh->do ("DROP TABLE IF EXISTS `ECM_Acts_VGPh3`.`TempTab`");

	$dbh->do ("CREATE TABLE `ECM_Acts_VGPh3`.`TempTab` (
 		`WITN1` varchar(10) NOT NULL default '',
	 	`WITN2` varchar(10) NOT NULL default '',
 		`DIR` varchar(4) NOT NULL default '',
 		`NR` int(3) NOT NULL default '0',
 		`MS1` int(6) NOT NULL default '0',
	 	`MS2` int(6) NOT NULL default '0',
 		`EQ` int(4) NOT NULL default '0',
	 	`W1FW2` int(4) NOT NULL default '0',
 		`W1TW2` int(4) NOT NULL default '0',
	 	`UNCLEAR` int(4) NOT NULL default '0',
 		`NOREL` int(4) NOT NULL default '0',
	 	`PASSAGES` int(4) NOT NULL default '0',
 		`DIFF` int(7) NOT NULL default '0',
	 	`PERC1` decimal(6,3) NOT NULL default '0.000',
 		`PERC2` decimal(6,3) NOT NULL default '0.000',
	 	`PERC3` decimal(6,3) NOT NULL default '0.000',
 		`PERC4` decimal(6,3) NOT NULL default '0.000',
	 	`CHECK` char(1) NOT NULL default ''
		) ENGINE=MyISAM DEFAULT CHARSET=latin1");

	$dbh->do ("INSERT INTO `ECM_Acts_VGPh3`.`TempTab` 
					SELECT  * FROM `ECM_Acts_VGPh3`.`$bs` 
					WHERE (MS1='$ms' AND (DIR='-->' OR DIR=' ')) OR (MS2='$ms' AND (DIR='<--' OR DIR=' '))
					");


	$sth = $dbh->prepare ("SELECT WITN1, WITN2, DIR, MS1, MS2, W1FW2, W1TW2, PERC2, PERC3 FROM `ECM_Acts_VGPh3`.`TempTab`");
	$sth->execute();

	### $ms will take the place of WITN1/MS1 in all rows. The content of all relevant fields 
	### is transposed accordingly.
	### 'fetchrow' triggers fields in the following sequence:
	###	$ary[0] WITN1, [1] WITN2, [2] DIR, [3] MS1, [4] MS2, [5] W1FW2, [6] W1TW2, [7] PERC2, [8] PERC3.

#	my @ary;

	while (@ary = $sth->fetchrow_array())
	{	
		#if ($ary[4]=$ms) { # das ist keine Überprüfung auf Gleichheit, sondern eine Zuweisung
		if ($ary[4] eq $ms) {
			
			$dbh->do ("UPDATE `ECM_Acts_VGPh3`.`TempTab` SET
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
		 
		 $dbh->do ("UPDATE `ECM_Acts_VGPh3`.`TempTab` SET DIR='<--'
					WHERE MS1='$ary[4]' AND MS2='$ary[3]';");
		}
		 
		 if ($ary[2] eq '<--') {
		 
		 $dbh->do ("UPDATE `ECM_Acts_VGPh3`.`TempTab` SET DIR='-->'
					WHERE MS1='$ary[4]' AND MS2='$ary[3]';");
		}
		
	}

	$dbh->do ("DROP TABLE IF EXISTS `ECM_Acts_VGPh3`.`PotDescendants`");

	$dbh->do("CREATE TABLE `ECM_Acts_VGPh3`.`PotDescendants` (
 		`WITN1` varchar(10) NOT NULL default '',
 		`DIR` varchar(4) NOT NULL default '',
 		`WITN2` varchar(10) NOT NULL default '',
	 	`NR` int(3) NOT NULL default '0',
 		`MS1` int(6) NOT NULL default '0',
	 	`MS2` int(6) NOT NULL default '0',
 		`PERC1` decimal(6,3) NOT NULL default '0.000',
	 	`EQ` int(4) NOT NULL default '0',
 		`PERC2` decimal(6,3) NOT NULL default '0.000',
	 	`W1FW2` int(4) NOT NULL default '0',
 		`PERC3` decimal(6,3) NOT NULL default '0.000',
	 	`W1TW2` int(4) NOT NULL default '0',
 		`PERC4` decimal(6,3) NOT NULL default '0.000',
	 	`UNCLEAR` int(4) NOT NULL default '0',
 		`NOREL` int(4) NOT NULL default '0',
	 	`PASSAGES` int(4) NOT NULL default '0'
		) ENGINE=MyISAM DEFAULT CHARSET=latin1");

	$dbh->do ("INSERT INTO `ECM_Acts_VGPh3`.`PotDescendants` 
			SELECT  WITN1, DIR, WITN2, NR, MS1, MS2, PERC1, EQ, PERC2, W1FW2, PERC3, 
			W1TW2, PERC4, UNCLEAR, NOREL, PASSAGES 
			FROM `ECM_Acts_VGPh3`.`TempTab` 
			ORDER BY `PERC1` DESC, `MS2` ASC
			");


### number pot. descendants

	my $msa=1;
	my $msb=1;
	my $count=1;
	my $perc1;
	my @ary3;


	$sth = $dbh->prepare ("SELECT * FROM `ECM_Acts_VGPh3`.`PotDescendants`
						#0 WITN1, 1 DIR, 2 WITN2, 3 NR, 6 PERC1, 7 EQ, 15 STELLEN 
						");
	$sth->execute();

##$rounded = sprintf("%.2f"", $unrounded);

	while (@ary3=$sth->fetchrow_array()) 
	{
		if ($ary3[1] eq '-->' and $ary3[15]>$min) 
		{ 	
##The ms compared with $ms will be counted as pot. descendant only if the number of passages 
##extant in both mss exceeds the threshold value $min. Thus the program will look for potential
##descendants of small fragments, but will exclude them from comparison when it looks for pot.
##descendants of more extensive documents. The reason is that small fragments have a much higher
##chance to reach high percentages of agreement and priority when compared with fuller mss.
			if ($count == 1) 
			{
				$perc1 = sprintf("%.$dec", $ary3[6]);			##round to decimal places according to
				$count++;										##selected base ($bs)
				$dbh->do ("UPDATE `ECM_Acts_VGPh3`.`PotDescendants` SET	
							NR='$msa'
							WHERE WITN2='$ary3[2]';");
			} else {										
			
				if (sprintf("%.$dec", $ary3[6]) == $perc1)  
				{
					$msb++;
					$dbh->do ("UPDATE `ECM_Acts_VGPh3`.`PotDescendants` SET
							NR='$msa'
							WHERE WITN2='$ary3[2]';");
				} 
				else 
				{
				$perc1=sprintf("%.$dec", $ary3[6]);
				$msb++;
				$msa=$msb;
				$dbh->do ("UPDATE `ECM_Acts_VGPh3`.`PotDescendants` SET
							NR='$msa'
							WHERE WITN2='$ary3[2]';");
				} # if/else
			} # if/else
		} # if	
	} # while

} # sub
