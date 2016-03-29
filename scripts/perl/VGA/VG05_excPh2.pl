#! /usr/bin/perl -w
# VG05_exc.pl -- MySQL:ECM_Acts_VG:ivv7srv16.uni-muenster.de
# füllt entspr. Tabelle mit den VGMS an, die mit MS häufiger übereinstimmen, als MS mit dem MT, sofern sie mindestens an der Hälfte der in MS belegten Teststellen gemeinsam Text haben

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_VG:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my $DEBUG = 0;
###Chapter Number eintragen (0 bzw. '' für Summierung)###
my $chn = $ARGV[0];
my $chnstr = '';

if ($chn < 10)
{
	if ($chn == 0)
	{
		$chnstr = '0';
	} else {
		$chnstr = '0'.$chn;
	}
} else {
	$chnstr = $chn;
}
my $source = '`ECM_Acts_VGPh2`.`VG05_all`';
my $wert = '`ECM_Acts_Mss`.`ActsMsListValPh2`';
my $target = '`ECM_Acts_VGPh2`.`VG05'.$chnstr.'_exc`';

my $sumtxtn;
my $qmtn;
my $gtxtn;
my $uegesn;
my $uegesqn;

if ($chn > 0)
{
	$sumtxtn = 'SUMTXT'.$chn;
	$qmtn = 'QMT'.$chn;
	$gtxtn = 'GTXT'.$chn;
	$uegesn = 'UEGES'.$chn;
	$uegesqn = 'UEGESQ'.$chn;
} else { # Summierung
	$sumtxtn = 'SUMTXT';
	$qmtn = 'QMT';
	$gtxtn = 'GTXT';
	$uegesn = 'UEGES';
	$uegesqn = 'UEGESQ';
}

my $sql = "DROP TABLE IF EXISTS $target;";
if ($DEBUG) { print "\n$sql"; }
$dbh->do ($sql);

$sql = "CREATE  TABLE  $target 
         (`MS` int( 6  )  NOT  NULL ,
	 `VGMS` int( 6  )  NOT  NULL ,
	 `CHECK` varchar( 1  )  NOT  NULL ,
	 `GTXT` int( 5  )  NOT  NULL ,
	 `UEGES` int( 5  )  NOT  NULL ,
	 `UEGESQ` decimal( 4, 1  )  NOT  NULL ,
	 KEY  `MS` (  `MS`  ) ,
	 KEY  `VGMS` (  `VGMS`  )  ) ENGINE  =  MyISAM  DEFAULT CHARSET  = latin1;";
if ($DEBUG) { print "\n$sql"; }
$dbh->do ($sql);

my ($sth, @ary, $ary, $hsnr, @msl, $ms, $limit, $qmt);

$dbh->do ("UPDATE $wert SET `CHECK` = '' WHERE 1");

$sth = $dbh->prepare ("SELECT HSNR FROM $wert WHERE `CHECK` NOT LIKE 'e'");
$sth->execute();
	
while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
}

foreach $ms(@msl)
{
	undef $sth;
	($limit, $qmt) = $dbh->selectrow_array ("SELECT $sumtxtn, $qmtn FROM $wert WHERE HSNR = $ms");
	
	$sth = $dbh->prepare ("SELECT `MS`, `CHECK`, `VGMS`, $gtxtn, $uegesn, $uegesqn FROM $source WHERE (`MS` = $ms OR `VGMS`= $ms) AND $gtxtn > $limit/2 AND $uegesqn > $qmt ORDER BY $uegesqn DESC");
	
	$sth->execute();
	
	if (defined $sth)
	{
		while (@ary = $sth->fetchrow_array())
		{
			if ($ms == $ary[0])
			{
				$dbh->do ("INSERT INTO $target (MS, `CHECK`, VGMS, GTXT, UEGES, UEGESQ) 
				VALUES ($ary[0], '$ary[1]', $ary[2], $ary[3], $ary[4], $ary[5])");
			} else {
				$dbh->do ("INSERT INTO $target (MS, `CHECK`, VGMS, GTXT, UEGES, UEGESQ) 
				VALUES ($ary[2], '$ary[1]', $ary[0], $ary[3], $ary[4], $ary[5])");				
			}
		}
	}
			
	$dbh->do ("UPDATE $wert SET `CHECK` = 'e' WHERE HSNR = $ms");
}

$sth->finish ();

$dbh->disconnect ();

exit (0);
