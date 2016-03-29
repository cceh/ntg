#! /usr/bin/perl -w
# Acts_Rel.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# show the variants attested by the closest relatives of all witnesses of a reading at a specified passage in Jn 18 Subset
# the closest relatives are stored in `ECM_Acts_VG`.`VG05<n>_exc 

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_CBGM:localhost";	# data source name, 'localhost' fits at any time!
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

#CHECKIN
#print "<br>Welcome to Acts_Rel.<br>";
#print "<br>$ARGV[0]<br>";

my $db = '`ECM_Acts_CBGM`';
my $list = '`ECM_Acts_Mss`.`ActsMsList`';

my ($writ, $ds, $bc, $bv, $bw, $ec, $ev, $ew, $var, $gr, $mt, $sk, $rnlim, $ba, $ea, $exc, $cstr);

($writ, $bc, $bv, $bw, $ec, $ev, $ew, $var, $gr, $mt, $sk, $rnlim, $ba, $ea) = $dbh->selectrow_array ("SELECT WRT, BC, BV, BW, EC, EV, EW, VAR, GR, MT, SK, RELNR, BEGADR, ENDADR FROM $db.`PreCoActs_Log` WHERE ID = $ARGV[0]");

#print "$writ, $bc, $bv, $bw, $ec, $ev, $ew, $var, $gr, $mt, $sk, $rnlim, $ba, $ea";

my $writc = 'Acts';
if ($bc<10)
{
	$cstr = '0'.$bc;
} else {
	$cstr = $bc;
}

my $att = '`Acts'.$cstr.'att`';

#Statusfeld in ActsMsList
my $mlf = '`Apg'.$cstr.'`';

if ($sk == 1)
{
	$exc = '`ECM_Acts_VG`.`VG05'.$cstr.'_exc`';
} else {
	$exc = '`ECM_Acts_VG`.`VG05_exc`';
}

my $dbsp = '`ECM_Acts_Sp_'.$cstr.'`';
my $wert = '`ECM_Acts_Mss`.`ActsMsListVal`';

my ($sth, @ary, $ary, @msl, $ms, @witn, $witn, $witc);

###extract the list of witnesses from Att table

my $test = $dbh->selectrow_array ("SELECT HSNR FROM $db.$att WHERE ANFADR = $ba AND ENDADR = $ea AND `LABEZ` LIKE '$var'"); # ECM_Acts_CBGM.ActsNNatt

unless (defined $test)
{
	print "<br>No witnesses found for $writ $bc:$bv/$bw - $ec:$ev/$ew in $att.";
	exit (0);
}

$sth = $dbh->prepare ("SELECT `HSNR` FROM $db.$att WHERE `ANFADR` = $ba AND `ENDADR` = $ea AND `LABEZ` LIKE '$var' ORDER BY `HSNR`"); # ECM_Acts_CBGM.ActsNNatt
$sth->execute();

###Supplements are excluded by the original script. I leave them in the table for Ch18

while (@ary = $sth->fetchrow_array())
{
	@witn = (@witn, $ary[0]);
} 

foreach $witn(@witn)
{
	my $rn = 0;
	my $rn2 = 0;
	my ($witc, $witqm);
	my $qmtc;
	if ($sk == 1)
	{
		$qmtc = 'QMT'.$bc;
	} else {
		$qmtc = 'QMT';
	}
	
	if ($sk == 2)
	{
		($witc, $witqm) = $dbh->selectrow_array ("SELECT HS, QMT FROM $wert WHERE HSNR = $witn"); # $wert = '`ECM_Acts_Mss`.`ActsMsListVal`'
	} else {
		($witc, $witqm) = $dbh->selectrow_array ("SELECT HS, $qmtc FROM $wert WHERE HSNR = $witn"); # $wert = '`ECM_Acts_Mss`.`ActsMsListVal`'
	}

	print "<br><strong>$witc - MT $witqm%</strong>";
	
###extract the list of relatives from relevant VG05_exc table ($exc)
	$sth = $dbh->prepare ("SELECT VGMS, UEGESQ FROM $exc WHERE MS = $witn ORDER BY UEGESQ DESC, VGMS ASC"); # $exc = '`ECM_Acts_VG`.`VG05(NN)_exc`'
	
	$sth->execute();
	unless (defined $sth)
	{
		print "<br>No relatives found for $witc in $exc.";
		exit (0);
	}

	while (@ary = $sth->fetchrow_array())
	{
		@msl = (@msl, $ary[0]);
	} 

	foreach $ms(@msl)
	{
		my $testms = $dbh->selectrow_array ("SELECT `MS` FROM $list WHERE `MS` = $ms AND $mlf = 1"); # $list = '`ECM_Acts_Mss`.`ActsMsList`'
		unless (defined $testms)
		{
			next;
		}
		
		my ($mstab, $uegesq, $msqm, $msc);

		if ($sk == 1)
		{
			($msc, $msqm) = $dbh->selectrow_array ("SELECT HS, QMT FROM $wert WHERE HSNR = $ms"); # $wert = '`ECM_Acts_Mss`.`ActsMsListVal`'
		} else {
			($msc, $msqm) = $dbh->selectrow_array ("SELECT HS, $qmtc FROM $wert WHERE HSNR = $ms");
		}

		$uegesq = $dbh->selectrow_array ("SELECT UEGESQ FROM $exc WHERE MS = $witn AND VGMS = $ms");
			
		$mstab = $dbsp.'.`Acts'.$cstr.'_'.$ms.'`';
		
		my ($rdg2, $byz);
		($rdg2, $byz) = $dbh->selectrow_array ("SELECT `LABEZ`, `BYZ` FROM $mstab WHERE `ANFADR` = $ba AND `ENDADR` = $ea");
	
			unless ($rdg2 =~ /zu|zv|zw|zx|zy|zz/)
			{
				# running number
				$rn++;
				$rn2++;
				if (defined $byz)
				{
					if ($byz eq 'B')
					{
						$rdg2 = $rdg2.' (M)';
					}
				}
				if ($gr == 2 and $uegesq <= $msqm)
				{
					$rn2 = $rn2-1;
					next;
				}
			
				if ($rdg2 =~ /M/ and $mt == 2)
				{
					$rn2 = $rn2-1;
					#to keep the running numbers of relatives, but stop at 	$rnlim
					if ($rn2 == $rnlim)
					{
						undef $rn;
						undef $rn2;
						last;
					} else {
						next;
					}
				
				} else {
					print "<br>$rn2 - $rn) $msc - $uegesq - $rdg2";
				}
			}
		
#			if ($mt == 2)
#			{
				if ($rn2==$rnlim)
				{
					undef $rn;
					undef $rn2;
					last;
				}
#			} else {
#				if ($rn==$rnlim)
#				{
#					undef $rn;
#					undef $rn2;
#					last;
#				}
#			}
		
		} #foreach $ms(@msl)
	
		undef @msl;
	
	
} #foreach $witn(@witn)

$sth->finish ();

$dbh->disconnect ();

exit (0);
